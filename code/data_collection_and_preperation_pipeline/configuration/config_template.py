"""
Master configuration file.
Add values to each property.
Do not remove any properties.

As of right now, only the Cluster is configured to be deployed automatically.
You must manually set up the RedShift and Aurora Databases
"""

class RedshiftWarehouseConfig:
    """ Configuration for the RedShift data warehouse """
    host = ''  # The Remote database Hostname
    user = ''  # The Database Username
    password = ''  # The Database Password
    database = "dev"  # database schema name
    port = 5439  # The Database Port (uses flavor-specific default if None)

    threads = 10  # max connection threads

    iam_s3_access_role = ""


class MysqlDatabaseConfig:
    """ Config for the transactional MySQL database """
    host = ""  # The Remote database Hostname
    user = ""  # The Database Username
    password = ""  # The Database Password
    database = ""  # database schema name
    port = 3306  # The Database Port (uses flavor-specific default if None)

    threads = 10  # max connection threads


class Cluster:
    """ Config for the AWS computing cluster """
    ssh_key = ""  # SSH
    subnet = ""  # AWS subnet ID

    region = "us-east-1"
    name = "slurm-cluster"
    storage_size = 100  # GiB
    storage_path = "/shared"

    os = "ubuntu2004"
    head_instance = "t2.2xlarge"  # EC2 instnace type for the head node
    instance = "c6i.4xlarge"  # EC2 instance type to use for worker nodes
    max_nodes = 100  # maximum number of nodes to deploy

    # paths to exclude from file transfer to the cluster
    exclude_paths = ["venv/", "local/", "data/*"]


class Mail:
    """ Config for the Mail utility """
    email_to = ""  # email to send notifications to

    # AWS credentials to send mail from
    email_from = ""  # email that will do the sending
    AWS_region = ""
    AWS_key_id = ""
    AWS_key = ""


class Config:
    """ Main Configuration Parameters """
    mail = Mail
    cluster = Cluster
    mysql = MysqlDatabaseConfig
    redshift = RedshiftWarehouseConfig

    # AWS S3 Bucket for intermediate data storage
    s3_bucket = ""

    # NCBI API
    NCBI_API_key = ""
    NCBI_rate_limit = 10

    # UMLS API
    UMLS_username = ""
    UMLS_API_KEY = ""

    debug = False  # enable debug mode
    repo_directory = "brainworks-public"
    log_directory = "logs/brain-log"
    data_directory = "data"  # data storage directory

    # NLP Pipeline config
    coreference_resolution_model = "https://storage.googleapis.com/allennlp-public-models/coref-spanbert-large-2021.03.10.tar.gz"
    ner_models = ["en_core_sci_scibert"]  # list of SciSpacy NER models

    # CoreNLP Server
    CoreNLP_memory = "8G"
    CoreNLP_endpoint = 'http://localhost:9000'
    CoreNLP_properties = {  # CoreNLP Server properties
        "annotators": "tokenize,ssplit,pos,lemma,depparse,openie",  # OpenIE Configuration
        "openie.max_entailments_per_clause": "1",
        "openie.triple.strict": "false",
        "openie.triple.all_nominals": "true",
        "openie.threads": 8,
        "tokenize.options": "splitHyphenated=false,splitAssimilations=false",  # don't split hyphenated words or words like "gonna"
    }