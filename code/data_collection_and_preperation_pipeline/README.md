# Guide to using this repository
This repository contains all source code necessary to recreate the databases used by the BRAINWORKS project.

### Build Instructions
The following is a list of step-by-step instructions to build the infrastructure necessary to run the platform. 
This documentation assumes basic knowledge of the command-line for your computer's operating system as well as Ubuntu, as it will be necessary for this process. It is also assumed that the AWS account in use has all the permissions necessary to deploy the infrastructure required for the project.

We recommend having a document open on your computer into which you can paste various API keys, URLs, usernames, and passwords, as you will be creating these items throughout the process and they will be need to be saved and later pasted into a configuration file at the very end.

1. AWS account
   - [Register](https://aws.amazon.com/) for an AWS account (or login to one you already have).
   - Visit the AWS IAM service page and generate access key credentials with Admin privileges.
   - Add your access key and secret access key to your `~/.aws/credentials` file, or use `aws init` using the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html)
   - Copy your access key and secret access key for later.
   - Make sure your AWS account has root permission or the necessary permissions to perform all actions outlined in the following steps, and additionally to deploy a Parallel Compute Cluster via cloudformation.

The following instructions may have two options:

**Option A**: (Recommended) You are creating the platform to run outside a VPC, like a Lightsail instance.\
**Option B**: You are creating the platform to run on a private server inside a VPC, Like an EC2 instance. This option requires that you or your organization have the ability to access the private IP address of deployed EC2 instances through the use of a VPN.

All steps will include the options **A** or **B** where applicable. **Choose only 1 option**, depending on which situation applies to you. If a step does not have either, it applies to both situations.

2. Acquire a VPC
   - Go to the AWS `VPC` service page
   - On the left sice panel, select `Your VPCs`
   - **A**: If you already have a VPC, you do not need to create one, but it must have a public subnet.
   - **B**: If you already have a VPC, you do not need to create one, and it does not need a public subnet.
   - If you don't have a VPC, click `Create VPC`
   - Choose `VPC and more`
   - Click `Create VPC`


3. Create an S3 Bucket
   - Go to the AWS `S3` service page
   - On the left side panel, click `buckets`
   - Click `Create Bucket`
   - Once created, select the bucket and click `Properties`
   - Copy the ARN of the bucket and put it somewhere for later


4. Create IAM Policy for Aurora to access the S3 bucket.
    - Go to the AWS `IAM` service page
    - On the left side panel, select `Policies`
    - Click `Create Policy`
    - Select the `JSON` tab
    - Paste in the following text, but in the `Resources` section, replace `BUCKET-ARN` with the S3 bucket ARN you copied from Step 3. The first line should still have `/*` at the end and the second one should just be the ARN.
    ```
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowAuroraAccessToBrainworksBucket",
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:AbortMultipartUpload",
                    "s3:ListBucket",
                    "s3:DeleteObject",
                    "s3:GetObjectVersion",
                    "s3:ListMultipartUploadParts"
                ],
                "Resource": [
                    "BUCKET-ARN/*",
                    "BUCKET-ARN"
                ]
            }
        ]
    }
    ```
   - Click `Next: Tags`
   - Click `Next: Review`
   - Provide a name and description for this policy. Copy the name for Step 5.
   - Click `Create Policy`


5. Create an IAM Role for Aurora to access the S3 bucket.
   - Go to the AWS `IAM` service page
   - On the left side panel, choose `Roles`
   - Click `Create Role`
   - Under the `Use case` dropdown, choose `RDS`
   - Select `RDS - Add Role to Database`
   - Click `Next`
   - On the `Permissions policies` page, enter the name of the policy you created in Step 4 into the search field, and select it when it appears (click the checkbox next to it).
   - Click `Next`
   - Provide a name and description for this Role.
   - Click `Create Role` at the bottom of the page
   - Click `View Role` at the top of the page. If you don't see this option, use the search bar to search for the name you gave the role and click it.
   - Copy the ARN for the next step.


6. Create an Aurora Parameter Group
     - Go to the AWS `RDS` service page
     - On the left side panel, select `Parameter Groups`
     - CLick `Create Parameter Group`
     - In the `Parameter Group Family` dropdown, choose `aurora-mysql8.0`
     - In the `Type` choose `DB Cluster Parameter Group`
     - Provide a name and description for this parameter group. Remember or copy the name for step 7.
     - Click `Create`
     - Click the parameter group you just created, which will take you to the `Parameters` page.
     - In the `Filter Parameters` field, type `aws_default_s3_role`
     - Click `Edit parameters`
     - Enter the ARN for the role you created in Step 5 into the value for the parameter
     - Click `Save changes`


7. Create an Aurora MySQL database
     - Go to the AWS `RDS` service page
     - Click `Create database`
     - In the `Engine Options` section:
       - Select `Amazon Aurora`
       - Toggle the switch that says `Show versions that support Serverless v2`
       - From the `Available Versions` dropdown, select `Aurora MySQL 3.02.2`
     - In the `Settings` section:
       - Provide a cluster name as you wish
       - Create a master username and password, and save them somewhere for later. (**Do not** autogenerate a password.)
     - In the `Instance Configuration` section:
       - Choose `Serverless`
     - In the `Availability & durability` section:
       - Choose `Don't create an Aurora Replica`
     - In the `Connectivity` section:
       - Choose the VPC you created in Step 2.
       - **A**: Under `Public Access` choose `Yes`
       - **B**: Under `Public Access` choose `No`
     - In the `Additional Configuration` section:\
       *note: This is a whole new section. There are sections labeled "Additional Configurations" which are part of other sections, but this is the completely separate section titled "Additional Configuration" at the very bottom.*
       - Under `Initial Database Name`, provide a new database name (different than the cluster name you created earlier). Remember or copy this for later.
       - In the `DB cluster parameter group` drop down, select the Parameter Group that you created in Step 6.
     - Click `Create database`
     - Click the `Regional Cluster` that contains the database that is currently being created.
     - In the `Connectivity & Security` tab, under `Manage IAM Roles`, select `Select IAM roles to add to this cluster`
     - Select the role you created in Step 5, and click `Add role`


8. Create a RedShift database
     - Go to the `RedShift` service page 
     - On the left side panel, click `Configurations`, then `Subnet Groups`
     - Click `Create cluster subnet group`
     - Provide a name and description as you wish
     - Select the VPC you created, and click `Add all the subnets for this VPC`
     - Click `Create cluster subnet group`
     - On the left side panel, go to `Clusters`
     - Click `Create Cluster`
     - In the `Cluster Configuration` section:
       - Name the cluster as you wish
       - Choose an appropriate node type and number. Large nodes or more nodes will be more costly, but more efficient.
     - In the `Database Configuration` section:
       - Choose a master username and password, and save them somewhere for later. **Do not** autogenerate a password.
     - In the `Additional Configurations` section:
       - Toggle OFF the switch that says `use defaults`
       - Click `Network and Security`
       - Choose the VPC you created
       - **A**: Check `Turn on publicly accessible`
       - **B**: Turn **OFF** `Turn on publickly accessible` if it isn't already
     - Click `Create Cluster`
     - Once cluster is created, select the cluster.
     - In the `General Information` section, copy the `Endpoint` string and save for later.
     - Go to the `Properties` tab
     - Scroll down to the `Associated IAM roles` section
     - On the right, click `Manage IAM roles` then `Create IAM role`
     - Select `Specific S3 buckets`
     - Choose the bucket you created in Step 3.
     - Click `Create IAM role as default`
     - Click the newly added role, which will take you to the role's page.
     - Copy the ARN for this role. It should look something like `arn:aws:iam::account_number:role/service-role/AmazonRedshift-CommandsAccessRole-some_more_numbers_here`
     - Save this for later.


9. Create an SSH Key Pair
   - Go to the AWS `EC2` management console.
   - On the left side panel, under `Network and Security`, click `Key Pairs`
   - Click `Create key pair`
   - Provide a name, then click `Create key pair`.
   - Download the private key file when prompted.
   - Place the private key you just downloaded into your local .ssh directory, typically located at `~/.ssh/`
    

10. Create a Compute Instance
   - **Option A**: Create a Lightsail instance
     - Go to the AWS `Lightsail` service page
     - Click `Create Instance`
     - Select `Linux / Unix`
     - Select `Os Only`
     - Select `Ubuntu 20.04 LTS`
     - In the `Optional` section, click `Change SSH key pair`
     - Choose `Default key` Note: this is *not* the same key you created earlier. They are unrelated.
     - Choose an instance type. It is recommended to use the instance with 32 GB memory.
     - Name your instance and click `Create Instance` at the bottom. The instance will start creating.
     - At the top right, click `Account` and select `Account` from the dropdown
     - Select `SSH Keys`
     - In the section titled `Default keys`, you should see one key. Click the download button for that key.
     - Place the downloaded private key in your local .ssh directory, typically located at `~/.ssh/`
     - Once the instance has been created, select the instance.
     - Go to the `Networking` tab
     - Under `IPv4 networking` click `Attach static IP`
     - From the dropdown, click `Create a new static IP`, and provide a name
     - Click `Create and attach`
     - Copy the new Public IP assigned to your instance
     - Open the terminal application on your computer.
     - SSH into the instance from your terminal. For example, for a Windows computer you would use the following command, replacing the ssh key file name with the one you just downloaded, and the IP address with the static IP you just attached: `ssh -i ~/.ssh/downloaded_default_key.pem ubuntu@static_ip`
     - Once connected to the server, clone this git repository using `git clone <repo_url_here>`
     - Once complete, move and rename the `pipeline` directory to the home folder using `cp path_to_pipeline ~/brainworks-public`
     - Do the same for the `website` directory, using `cp repo_name/website brainworks-website`
     - Navigate into the copied directory: `cd brainworks-public`
     - Run the following command: `bash setup.sh`. This will install all necessary software dependencies for the project.
   - **Option B**: Create an EC2 Instance
     - Go to the AWS `EC2` service page
     - On the left side panel, select `Instances`
     - Click `Launch Instances`
     - Provide a name for this instance
     - Select `Ubuntu`
     - In the next dropdown, select `Ubuntu Server 22.04 LTS (HVM), SSD Volume Type`
     - In the `Instance type` section, we recommend selecting `t2.2xlarge`
     - In the `Key pair` section, select the key pair you created in Step 9.
     - In the `Network` section, click `Edit`
     - Select the VPC you created in Step 2.
     - Click `Launch Instance`
     - Once created, you need to add the ability to connect to you Aurora and Redshift databases:
       - On the left side panel, select `instances`
       - Click the underlined ID of the instance you have created.
       - Click `Actions`, then `Networking`, then `Connect RDS database`
       - From the dropdown meny, select the Aurora database you created in Step 7.
       - Click `Connect`
       - Now go to the AWS `RedShift` service page
       - Select the cluster you created in Step 8.
       - Click the `properties` tab
       - Copy the ID of the `VPC Security Group`
       - Return to your EC2 instance
       - Click `Actions`, then `Security`, then `Change security groups`
       - In the `Associated Security Groups` section, paste the RedShift security group ID you copied
       - Click `Add security group`
       - At the bottom of the page, click `Save`
     - Return to the EC2 instance page. Click `Connect to your instance`
     - Select the `SSH Client` tab
     - Copy the private IP address from item number 4.
     - Open the terminal application on your computer.
     - Note: This next step is only possible if you satisfy the conditions of Option B as stated at the beginning of this documentation; i.e. You or your organization has the ability to connect to the private IP addresses of deployed EC2 instances within the VPC.
     - SSH into the instance from your terminal. For example, for a Windows computer you would use the following command, replacing the ssh key file name with the one you downloaded in Step 9, and the IP with the private IP you just copied: `ssh -i ~/.ssh/downloaded_key.pem ubuntu@private_ip`
     - Once connected to the server, clone this git repository using `git clone <repo_url_here>`
     - Once complete, move and rename the `pipeline` directory to the home folder using `cp repo_name/pipeline brainworks-public`
     - Do the same for the `website` directory, using `cp repo_name/website brainworks-website`
     - Navigate into the copied directory: `cd brainworks-public`
     - Run the following command: `bash setup.sh`. This will install all necessary software dependencies for the project.

11. UMLS API Account
   - [Register](https://uts.nlm.nih.gov/uts/login) for a NLM account (or login).
   - Under `UTS Profile` panel on the right, click `Generate an API Key`.
   - Complete the form and save the `API Key` listed for later
   - Download [UMLS Metathesaurus](https://www.nlm.nih.gov/research/umls/licensedcontent/umlsknowledgesources.html) dataset. Specifcally the 2021AB-Full dataset.
   - The files necessary for this project are MRCONSO.RRF, MRDEF.RRF, and MRHIER.RRF
   - Once these files are downloaded, upload them to the S3 bucket created in Step 3.


12. NCBI API
   - [Register](https://www.ncbi.nlm.nih.gov/account/) for an NCBI account (or login).
   - Navigate to the `settings` page by clicking your username in the top-right corner. 
   - Under the `API Key Management` section click `Create an API Key`
   - Save the given key for later.


### Configuration
Here you will provide all the database names, usernames, passwords, and keys that you have saved from the steps above.
13. SSH into the compute instance from your terminal as done in Step 10.
   - Navigate to the `brainworks-public` directory with the following command: `cd brainworks-public`
14. Copy the template configuration file using the following command: `cp configuration/config_template.py configuration/config.py`. This new file is where your sensitive API keys and database password will go.
15. Now edit the file. You may do this by using [Vim](https://www.vim.org/docs.php) on the remote instance using the following command: `vim configuration/config.py`. You can also choose to download the file using [SFTP](https://cat.pdx.edu/platforms/linux/remote-access/using-sftp-for-remote-file-transfer-from-command-line/) and edit it locally, then upload the file once you are finished.
16. Edit the configuration options as described below in steps 17 - 20, where you will be pasting information about the infrastructure you have set up.

17. RedshiftWarehouseConfig:
    - Go to the AWS `RedShift dashboard`
    - Click `Clusters` and select the cluster you created in step 3.
    - Copy the `Endpoint` string from the right side of the General Information section.
    - Paste the string into the `host` field.
    - It should look something like `cluster-name.ksmsjcdfi.us-east-1.redshift.amazonaws.com`. Note that you need to remove anything that appears after the `.com`
    - Provide the username and password you created earlier in the `user` and `password` fields, respectively.
    - The default schema is `dev`, which shouldn't have been changed. If you did, that goes in the `database` field.
    - The default port is `5439`, which shouldn't have been changed. If you did, that goes in the `port` field.


18. MySQLDatabaseConfig:
    - Go to the AWS `RDS` dashboard, and select `Databases` on the left side panel.
    - Select the Aurora database you created in Step 7.
    - In the `Connectivity & security` section, copy the `Endpoint` string.
    - Paste the string into the `host` field of the config.
    - It should look something like `aurora-name.djdfiwehnf.us-east-1.rds.amazonaws.com`. Note that you need to remove anything that appears after the `.com`
    - Provide the username and password you created earlier in the `user` and `password` fields, respectively.
    - Provide the `Initial Database Name` you created in step 7 in the `database` field.
    - The default port is `3306`, which shouldn't have been changed. If you did, that goes in the `port` field.


19. Cluster
   - Copy the SSH private key file you downloaded in Step 9 into `configuration/ssh/` on your remote compute instance. Do do this, use SFTP as explained in Step 15.
   - In the `ssh_key` field, put the exact name of that key file. It should look something like `name-of-file.pem`
   - Go to the AWS VPC management console and select `My VPCs`.
   - Choose a public subnet in the VPC and click on it to take you to the subnet page.
   - Copy the `Subnet ID` in the top left corner. It should look something like `subnet-0a2f41c2d523`.
   - Paste the subnet ID into the `subnet` field.


20. Config
   - `s3_bucket`: the name of the S3 bucket created in Step 3. Note: This is the **name**, not the ARN.
   - `NCBI_API_key`: The API key from NCBI you created.
   - `UMLS_username`: The username you created for your UMLS account.
   - `UMLS_API_KEY` : The API key you created for your UMLS account.


## Command Line Interface
To access the command line:
1. SSH into the EC2 instance / Lightsail instance.
2. Navigate to the project directory: `cd brainworks-public`
3. Activate the python environment: `. venv/bin/activate`
4. You may now run the CLI, invoked using the command `brain`
5. To see a list of commands, run `brain --help`
6. To see details on a particular command, use the `--help` flag. For example, `brain collect --help`


# About

## Information Layer

The Information layer of BRAINWORKS collects, processes, and stores publication data and meta-data from several publicly available data sources into a read-optimized [MySQL Relational Database](https://www.mysql.com/) and computation-optimized [RedShift Relational Data Warehouse](https://aws.amazon.com/redshift/) for downstream use and analysis. Below we provide a list of the specific data sources collected by the information layer, the specific code utilities written for their processing:

### PubMed

The [PubMed](https://pubmed.ncbi.nlm.nih.gov/) data comprises more than 33 million citations for biomedical literature from MEDLINE, life science journals, and online books. Citations may include links to full text content from PubMed Central and publisher web sites. Our [Pubmed data collection utility](utils/documentCollector/pubmed.py)  contains several methods that enable:

* Programmatic search and download of the PubMed archive based on search terms, grant ids, or other parameters.
* Parsing of heterogeneous PubMed XML documents into unified highly structured objects for storage in relational tables.
* Application of NLP and other algorithms at the point of download and ingestion including author affiliation parsing.
* Automatic generation of MySQL tables and supporting indices for read-optimized storage of collected data.
* Collection of all papers related to a set of papers (i.e. all papers that cite a set of papers).

### ExPORTER

The [ExPORTER](https://exporter.nih.gov/) data provides access to NIH-funded research projects and their affiliated publications and patents. Our [ExPORTER data collection utility](utils/documentCollector/exporter.py) contains several methods that enable:

* Parsing of heterogeneous .CSV files into unified structured objects for storage in relational tables.
* Automatic generation of MySQL tables and supporting indices for read-optimized storage of collected data.

### GRID

[GRID](https://www.grid.ac/) is a free and openly available global database of research-related organizations, cataloging research-related organizations and providing each with a unique and persistent identifier.Our [GRID data collection utility](utils/documentCollector/grid.py) contains several methods that enable:

* Parsing of .CSV files into unified structured objects for storage in relational tables.
* Automatic generation of MySQL tables and supporting indices for read-optimized storage of collected data.



## Algorithms Layer

The Algorithms layer of BRAINWORKS transforms unstructured free text data (including, but not limited to, the data collected by the information layer into [UMLS](https://www.nlm.nih.gov/research/umls/index.html) annotated [semantic triples](https://en.wikipedia.org/wiki/Semantic_triple). Following extraction, these semantic triples are stored in a read-optimized [MySQL Relational Database](https://www.mysql.com/). Below we discuss the pre-processing and information extraction pipelines of the algorithms layer:



### Preprocessing

The text preprocessing pipeline standardizes and cleanses the text for downstream information extraction (i.e. semantic triples) and entity recognition. Our [NLP Extractor](utils/extraction/text2Graph.py) utility builds on [Stanford's CORENLP Tool](https://stanfordnlp.github.io/CoreNLP/) to accomplish the following text pre-processing components:

* **Tokenization:** the separation of the text into smaller units called tokens; the tokens can be words, characters, or subwords. 
* **Parts of Speech tagging:** the annotation of each token in the text with a particular part of speech (noun, verb, adjective, etc.), based on both its definition and its context.
* **Lemmatization:** the simplification of tokens to their root words.
* **Dependency Parsing:** the analysis of the sentence grammatical structure to identify semantic dependencies between tokens.
* **Coreference resolution:** the identification and mapping of all expressions that refer to the same entity in a text. 



### Information Extraction

The information extraction (IE) pipeline in our [NLP Extractor](utils/extraction/extraction.py) utility transforms preprocessed text, into semantic triples with each element of the triple (subject, relation, object) mapped to one or more UMLS entries. The IE pipeline consists of three steps:

* **Triple candidate generation:** we apply [Stanford's OpenIE Tool](https://nlp.stanford.edu/software/openie.html) to extract a large set of semantic triple candidates. 
* **Named Entity Recognition:** we identify and annotate any existing UMLS entities in the extracted triple candidate using a [SciBERT Transformer](https://allenai.github.io/scispacy/). 
* **Minimal spanning set:**  Finally, we retain the minimal spanning set of triples; that is, the smallest possible subset of the triples that captures all UMLS relationships implied by the larger set. 

In this way, each triple reflects the relationships espoused by the original text, as well as the UMLS entities contained within them.







