import os, subprocess, inspect
from time import time, sleep
from datetime import datetime

from utils.base import Base

# The pcluster library is written in python so you can actually dig out the core functions
# That said, I really wish they made this more organized because it is clearly not designed for programmatic use.
from pcluster.api.pcluster_api import ApiFailure, PclusterApi
from pcluster.api.models.cluster_status import ClusterStatus as Status
from pcluster.api.models.cloud_formation_stack_status import CloudFormationStackStatus as CloudStatus
# TODO maybe try to use this awful code snippet https://docs.aws.amazon.com/parallelcluster/latest/ug/tutorials_06_API_use.html


class Cluster(Base):
    """ Utility to control deployment of the parallel computing cluster """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repo_dir = self.config.repo_directory

        self.region = self.config.cluster.region
        self.name = self.config.cluster.name

        self.instance = self.config.cluster.instance
        self.head_instance = self.config.cluster.head_instance
        self.subnet = self.config.cluster.subnet
        self.os = self.config.cluster.os
        self.max_nodes = self.config.cluster.max_nodes
        self.storage_size = self.config.cluster.storage_size  # GiB
        self.storage_path = self.config.cluster.storage_path
        self.ssh_key = self.config.cluster.ssh_key

        # paths to exclude from file transfers
        self.exclude_paths = self.config.cluster.exclude_paths

        self._ip = None  # cluster IP address

        # make sure ssh key perms are closed enough
        try:
            os.chmod(f"./configuration/ssh/{self.ssh_key}", 0o400)  # octal 400
        except FileNotFoundError as e:
            self.debug(e)
            self.log(f"The specified SSH key file, \"{self.ssh_key}\", was not found in ./configuration/ssh/")
            self.log("This will prevent you from creating the Cluster or performing any cluster operations.")

        self.api = PclusterApi()

    @property
    def ip(self):
        """ Get the cluster IP address """
        if not self._ip:
            ip = os.popen(f"""
                pcluster describe-cluster --cluster-name {self.name} --region {self.region} --query headNode.publicIpAddress  | tr -d '"\n'
            """).read()
            if "does not exist" in ip:
                self.throw("Could not get cluster IP - cluster does not exist")
            else:
                self.debug(f"Got cluster IP: [{ip}]")
                self._ip = ip
        return self._ip

    @property
    def status(self):
        """ Retrieves the current status of the cluster """
        response = self.api.describe_cluster(cluster_name=self.name, region=self.region)
        if isinstance(response, ApiFailure):
            self.throw(f"Error assessing status of cluster: {response.message}, {response.validation_failures}, {response.update_changes}")
        else:
            #self.debug(f"Cluster Status: {response}")
            return response.status

    def run_on_cluster(self, bash='', capture=False):
        """ Run the given bash commands on the cluster """
        bash = "source /etc/profile;"+bash  # add the cluster profile as a source. This allows using slurm commands.
        command = f"""pcluster ssh --cluster-name {self.name} --region {self.region} -i configuration/ssh/{self.ssh_key} -oStrictHostKeyChecking=no -t "{bash}" """
        try:
            if capture:
                return subprocess.run(command, shell=True, check=True, capture_output=True, text=True).stdout.strip("\n")
            else:
                subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            self.log(f"Cluster command error {e}")

    def ssh_to_cluster(self):
        """ Start an ssh session to the cluster """
        command = f"""pcluster ssh --cluster-name {self.name} --region {self.region} -i configuration/ssh/{self.ssh_key} -oStrictHostKeyChecking=no """
        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            self.log(f"Failed to create SSH connection to cluster. {e.__class__.__name__}: {e}")

    def check_config(self):
        """ Verifies that the cluster config has been properly constructed """
        all_present = bool(
            self.config.cluster.region and
            self.config.cluster.name and
            self.config.cluster.subnet and
            self.config.cluster.storage_size and
            self.config.cluster.storage_path and
            self.config.cluster.ssh_key and
            #self.config.cluster.AWS_key_id and
            #self.config.cluster.AWS_key and
            self.config.cluster.os and
            self.config.cluster.head_instance and
            self.config.cluster.instance and
            self.config.cluster.max_nodes and
            self.config.cluster.exclude_paths
        )
        if not all_present:
            return "Not all configuration options have been provided."
        return  # all good

    def copy_to_cluster(self):
        """ Copy the repository to the cluster """
        self.log("Copying repo to cluster...")
        exclude = ' '.join(f'--exclude "{path}"' for path in self.exclude_paths)

        # -a: archive mode. Copy everything recursively
        # -e: use ssh
        # -oStrictHostKeyChecking=no: don't ask for user input to verify the ssh key
        os.popen(f"""
            rsync -a -e "ssh -i ./configuration/ssh/{self.ssh_key} -oStrictHostKeyChecking=no" {exclude} ../{self.repo_dir} ubuntu@{self.ip}:~/
        """)
        self.log("Transfer Complete.")

    def setup_environ(self):
        """ Set up the environment on the cluster """
        self.log("Building environment on cluster... (this will several minutes)")
        self.run_on_cluster(f"cd {self.repo_dir}/cluster; bash setup.sh;")
        self.log("Cluster environment complete.")

    def deploy(self, n=None):
        """ Deploy the cluster with <n> nodes """
        if not n: n = self.max_nodes  # number of nodes to deploy
        config = self.construct_yaml(n)  # construct yaml config string
        self.log(f"Deploying cluster with {n} nodes")
        response = self.api.create_cluster(cluster_name=self.name, region=self.region, cluster_config=config)
        if isinstance(response, ApiFailure):
            self.throw(f"Error creating cluster: {response.message}")

    def wait_for_deploy(self, wait=10):
        """ Waits until the cluster is completely deployed """
        while self.status != Status.CREATE_COMPLETE:  # while still setting up
            if self.status in [Status.CREATE_FAILED, CloudStatus.ROLLBACK_IN_PROGRESS, CloudStatus.ROLLBACK_COMPLETE, CloudStatus.ROLLBACK_FAILED]:
                self.throw(f"Failed to deploy cluster. Please consult the AWS logs to determine the source of this error. Last Status was: {self.status}")

            self.log(f"Cluster status was: \"{self.status}\" (checking again in {wait}s)")
            sleep(wait)

        self.log(f"Cluster status was: \"{self.status}\"")
        self.log("Cluster successfully deployed.")

    def construct_yaml(self, n):
        """ Construct a cloudformation yaml string to build a cluster with <n> nodes """
        key_name = self.ssh_key.split('.')[0]  # We assume that the ssh key name is the same as the file name without the extension
        yaml = f"""Region: {self.region}
Image:
  Os: {self.os}
HeadNode:
  InstanceType: {self.head_instance}
  Networking:
    SubnetId: {self.subnet}
  Ssh:
    KeyName: {key_name}
Scheduling:
  Scheduler: slurm
  SlurmQueues:
  - Name: q1
    ComputeResources:
    - Name: worker-node
      InstanceType: {self.instance}
      MinCount: 0
      MaxCount: {n}
    Networking:
      SubnetIds:
      - {self.subnet}
SharedStorage:
  - MountDir: {self.storage_path}
    Name: myebs
    StorageType: Ebs
    EbsSettings:
      VolumeType: gp3
      Size: {self.storage_size}"""

        #with open(self.template_file, "w") as file: file.write(yaml)
        #self.debug(f"Constructed CloudFormation template at: {self.template_file}")
        return yaml

    def delete(self):
        """ Delete the current cluster """
        response = self.api.delete_cluster(cluster_name=self.name, region=self.region)
        if isinstance(response, ApiFailure):
            self.throw(f"Failed to delete cluster. Error: {response.message}")
        elif self.status == Status.DELETE_IN_PROGRESS:
            self.log("Deleting Cluster...")
            return True
        else:
            self.throw(f"Cluster failed to delete. Status is: {self.status}")

    def wait_for_delete(self, wait=10):
        """ Waits until the cluster is completely deleted """
        while self.status == Status.DELETE_IN_PROGRESS:  # while still being detected
            self.log(f"Cluster status was: \"{self.status}\" (checking again in {wait}s)")
            sleep(wait)
        if self.status:  # cluster still connected means it wasn't deleted.
            self.throw(f"Failed to delete cluster. Last status was: {self.status}")
        else:
            self.log("Cluster Deleted.")


    ####
    # Slurm
    def run_slurm(self, start, end, test=False):
        """ Run extraction slurm jobs on the cluster """
        command = f"""
cd {self.config.repo_directory};
source cluster/venv/bin/activate;
python3 -c '
from datetime import date
from utils.extraction.extraction import NLPExtractor
from configuration.config import Config
config = Config()
config.debug = {self.config.debug}
start = date(year={start.year}, month={start.month}, day={start.day})
end = date(year={end.year}, month={end.month}, day={end.day})
ex = NLPExtractor(config)
ex.generate_paper_split(start_date=start, end_date=end, replace=False, benchmark={test})  # assign PMIDs to each node
ex.run_slurm()  # run slurm cluster
';
"""
        self.run_on_cluster(command)

    def get_slurm_jobs(self):
        """
        Returns how many slurm jobs are currently running on the cluster.
        Looks at how many lines are returned by the "squeue" command, and subtracts 1 for the header.
        """
        res = self.run_on_cluster("squeue | wc -l", capture=True)
        if res is not None:
            return int(res) - 1

    def wait_for_slurm(self, wait=30):
        """ Wait for all slurm jobs to complete """
        jobs = self.get_slurm_jobs()
        while jobs:  # jobs still running
            self.log(f"Slurm jobs running: {jobs} ... (checking again in {wait}s)")
            jobs = self.get_slurm_jobs()
            sleep(wait)

        self.log("All Slurm jobs complete.")

    def get_logs(self):
        """ Retrieve the slurm logs from the cluster """
        self.log("Retrieving Cluster Logs...")
        logdir = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")  # YYYY-mm-dd-H-M-S
        logdir = f"logs/cluster/{logdir}"
        self.ensure_path(logdir)
        command = f"""scp -r -i ./configuration/ssh/{self.ssh_key} -oStrictHostKeyChecking=no ubuntu@{self.ip}:/home/ubuntu/{self.repo_dir}/cluster/output {logdir}"""
        try:
            subprocess.run(command, shell=True, check=True)
            self.log(f"Retrieved Cluster logs, stored in: {logdir}")
        except subprocess.CalledProcessError as e:
            self.debug(f"Subprocess error: {e}")
            self.log("An error occurred while attempting to retrieve logs from the cluster.")


