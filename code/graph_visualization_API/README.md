Following are the instructions necessary to deploy an EC2 instance which hosts a local copy of the graph visualization API, which may be used by the BRAINWORKS application. These instructions will help you (1) stand up the API on an EC2 instance and (2) configure the BRAINWORKS application to use the new internal endpoint.

## Prerequisites
This documentation assumes that you have access to the AWS account which hosts the BRAINWORKS application, and you are connected to the NIH VPN. If you do not have access to this account, please contact the BRAINWORKS team for assistance. This documentation also assume that you have basic familiarity with software engineering principles, are able to edit files while accessing a remote server via CLI, and are familiar with the AWS console. 

## Step 1: Create an EC2 Instance
Follow these instructions to deploy an EC2 instance using the AWS console and upload the contents of this directory.
- Go to the AWS `EC2` service page
- On the left side panel, select `Instances`
- Click `Launch Instances`
- Provide a name for this instance
- Select `Ubuntu`
- In the next dropdown, select `Ubuntu Server 22.04 LTS (HVM), SSD Volume Type`
- In the `Instance type` section, we recommend selecting `t2.large`
- In the `Key pair` section, either create a new SSH key pair or use an existing one. If you create a new one, be sure to download the key pair file and store it in a safe place. You will need this file to SSH into the instance.
- In the `Network` section, click `Edit`
- Select the same VPC that houses the BRAINWORKS application. 
- Click `Launch Instance`
- Return to the EC2 instance page. Click `Connect to your instance`
- Select the `SSH Client` tab
- Copy the private IP address from item number 4.
- Open the terminal application on your computer.
- SSH into the instance from your terminal. For example, for a Windows computer you would use the following command, replacing the ssh key file you will using to connect, and the IP with the private IP you just copied: `ssh -i ~/.ssh/downloaded_key.pem ubuntu@private_ip`
- Once you have ensured that you are able to connect to the server, return to your local terminal and transfer this directory to the server using the following command (replacing the private IP of the EC2 instance and the private SSH key where applicable): `scp -i ~/.ssh/downloaded_key.pem -r ~/graph_api ubuntu@private_ip:~/`


## Step 2: Run the webserver for the API
The following instructions will be run on the EC2 instance created in step 1 to install the necessary software dependencies and run the webserver for the API.
- Once the transfer from Step 1 is complete, SSH into the EC2 instance and navigate into the directory you just transferred: `cd graph_api`
- Run the following command: `bash scripts/setup.sh`. This will install all necessary software dependencies for the code.
- Edit the NginX configuration file in `config/nginx.conf` and replace the IP address in the `server_name` field on line 10 with the private IP address of the EC2 instance from step 1. Save the file.
- Edit `config/domain_name.json` and replace the IP with the private IP address of the EC2 instance from step 1. Make sure to keep the `http://`. Save the file.
- Run the following command: `npm run build-production` This will create a new build of the API with the changes made.
- Run the following command: `bash scripts/run.sh`
- You should now be able to access the documentation page for the API by pasting the private IP address into your browser. If you have problems accessing the page, you may need to adjust your network interface security group settings on the EC2 instance to allow inbound traffic on port 80.
- Move on to step 3 only once you have confirmed that you are able to access this page.
- If you wish to deploy the web server using SSL and a dedicated domain name you will need to consult your IT department as this is beyond the scope on which we are able to advise. Doing so may involve editing the same two files as above. Once all changes are made, you should run the command `npm run build-production` followed by `bash scripts/reload.sh` to build and reload the API.

## Step 3: Configure the BRAINWORKS application to use the new API
The following instructinos will be run on the EC2 instance that hosts the BRAINWORKS application (**NOT the one you just created**). These instructions will configure the BRAINWORKS application to use the new API. Please note that you will need the IP address of the EC2 instance you created in Step 1, which will be referred to as the "GraphAPI-IP" in the following instructions.
- SSH into the remote EC2 instance that hosts the BRAINWORKS web application. For example, for a Windows computer you would use the following command, replacing the ssh key file you will using to connect, and the IP with the private IP of the EC2 instance: `ssh -i ~/.ssh/ssh_key.pem ubuntu@private_ip`.
- Navigate to the root directory of the BRAINWORKS application: `cd brainworks-website`
- Run the following command: `sudo pkill nginx` This will stop the webserver for the BRAINWORKS application.
- Run the following command: `sudo apt-get install npm -y`
- Run the following command: `cd react-app; sudo npm install; cd ../`
- Edit `config.py` and change the `GRAPH_API_URL` variable to the following: `GRAPH_API_URL = "http://GraphAPI-IP/build/0.0.2/js/graph.min.js"`, replacing the "GraphAPI-IP" with the value of the private IP address for the graph-api EC2 instance you configured in Step 1.
- Edit the file `react-app/env.production` and change the first line to the following: `REACT_APP_GRAPH_API_URL="http://GraphAPI-IP/build/0.0.2/js/graph.min.js"`, again replacing the "GraphAPI-IP" as before.
- Run the following command: `cd react-app; sudo npm run build-prod; cd ../` (this will take a few minutes). This will re-build the frontend of the BRAINWORKS application using the new API endpoint.
- Run the following command: `sudo nginx -c /home/ubuntu/brainworks-website/nginx.conf` This will start the webserver for the BRAINWORKS application using the new API endpoint.
```
