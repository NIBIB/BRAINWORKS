print("Executing....")

import click
import os, sys, math as m
from time import time, sleep
from datetime import date, timedelta
from functools import wraps
import itertools

from configuration.config import Config
from utils.base import Base, ThreadQueue
from utils.database.database import MySQLDatabase, RedShiftDatabase
from utils.mail import Mail
from utils.cluster import Cluster
from utils.pre_computed_tables import PreComputedTables

from utils.documentCollector.pubmed import PubmedCollector
from utils.documentCollector.icite import iCite
from utils.documentCollector.exporter import Exporter

config = Config

base = Base(config)
mail = Mail(config)
cluster = Cluster(config)

def email(func):
    """ Add the --email parameter """
    @click.option('--email', '-e', is_flag=True,  default=False,  help="If an email is given in the config, sends an email on failure or completion.")
    @wraps(func)
    def wrapper(*args, **kwargs):
        c = mail.config.mail
        if kwargs['email'] and not bool(c.email_to and c.AWS_region and c.AWS_key_id and c.AWS_key and c.email_from):
            mail.log("""You opted to receive an email when the command finished, but no email server has been provided in the config.\nEither remove the --email flag or provide the necessary configuration options.\nThen use the command "brain check-config --email" to send a test email and make sure it is functional.""")
            raise click.Abort()

        command_name = click.get_current_context().info_name
        param_info = 'Parameters\n' + '   \n'.join([f"{key}: {val}" for key,val in kwargs.items()])

        t0 = time()  # start time
        try:
            return func(*args, **kwargs)  # run the command
        except Exception as e:
            mail.debug(f"An uncaught error occurred: {mail.exc(e)}")
            total_time = mail.format_seconds(time()-t0)  # time diff string
            if kwargs['email']: mail.send(subject='BRAINWORKS Command Failed', body=f"The BRAINWORKS command \"{command_name}\" has failed.\n{param_info}\nElapsed Time: {total_time}\nStack Trace: \n{base.trace()}")
            raise e
    return wrapper

def debug(func):
    """ Adds the --debug parameter """
    @click.option('--debug', '-d', is_flag=True, default=False, help="Runs in debug mode (if not already set in the config)")
    @wraps(func)
    def wrapper(*args, **kwargs):
        if kwargs['debug']: config.debug = True
        return func(*args, **kwargs)
    return wrapper

@click.group()
def cli():
    pass


@cli.command()
@email
@debug
def check_config(email, debug):
    """
    Verify configuration options
    """
    if not bool(config.mail.email_to and config.mail.AWS_region and config.mail.AWS_key_id and config.mail.AWS_key and config.mail.email_from):
        print("Email: Not available. Not all email configuration options have been provided.")
    elif email:
        err = mail.send(subject="Test Email", body="If you received this, your email configuration is working properly.")
        if err:
            print(f"Email: There was a problem sending the test email to \"{config.mail.email_to}\". Please make sure you have properly set up your AWS email server.\nError: {base.exc(err)}")
        else:
            print(f"An email has been sent to \"{config.mail.email_to}\". Please confirm receipt to ensure that email notifications are functional.")
    else:
        print("Email: ok")

    err = cluster.check_config()
    if not err:
        print("Cluster: ok")
    else:
        print(f"Cluster: {err}")

    try:
        click.echo("Attempting to connect to MySQL database...")
        db = MySQLDatabase()
        rows = db.query('SELECT now()')
        print("MySQL DB: ok")
    except Exception as e:
        click.echo(f"Failed to create MySQL connection. {e.__class__.__name__}: {e}")

    try:
        click.echo("Attempting to connect to RedShift database...")
        db = RedShiftDatabase()
        rows = db.query('SELECT now()')
        print("RedShift DB: ok")
    except Exception as e:
        click.echo(f"Failed to create RedShift connection. {e.__class__.__name__}: {e}")


@cli.command()
@email
@debug
def get_doc_field_stats(email, debug):
    """ Generate JSON of all field statistics in collected publocations """
    t0 = time()
    pm = PubmedCollector(config)  # collector
    pm.get_document_field_stats()
    elapsed = pm.format_seconds(time()-t0)
    if email: mail.send(subject='Completed Field Stats', body=f"BRAINWORKS has finished analysing field stats of the stored documents.\nElapsed Time: {elapsed}")

@cli.command()
@debug
def clear_stored_pub_index(debug):
    """
    Used for debugging purposes.
    Clears the stored index of all files on disk, then re-indexes all files.
    Use this if you manually deleted some stored data files and are now getting FileNotFound Errors.
    """
    pm = PubmedCollector(debug)  # initialize
    filename = pm.stored_files.file
    del pm  # force the file to be saved
    os.remove(filename)  # remove the file
    base.log("removed index")
    pm = PubmedCollector(debug)  # re-initialize, and save

@cli.command()
@email
@debug
@click.option('--test', "-t", is_flag=True, default=False, help="Collects a very small dataset. Useful to check for problems before running with full data.")
@click.option('--start', default="1980/01/01", help="The start date for pulling publications. Format: YYYY/MM/DD")
@click.option('--end', help="The end date for pulling publications. Format: YYYY/MM/DD")
@click.option('--replace', is_flag=True, default=False, help="Wipe and repopulate the citation table. This ensures all citation stats are up-to-date")
def collect(start, end, replace, email, test, debug):
    """ Activate document collection pipeline """
    t0 = time()
    pm = PubmedCollector(config)  # collector

    if test:  # collect papers from a single day
        start = pm.validate_date("2000/01/02", format="%Y/%m/%d", throw=True)
        end = pm.validate_date("2000/01/02", format="%Y/%m/%d", throw=True)
        pm.db.query("SELECT now()")
        pm.log("Database connection successful.")
        pm.generateTables()  # create tables if they don't already exist
        pm.bulk_collect(start_date=start, end_date=end, replace=replace, reverse=True)
        pm.insert_papers(replace=replace, reverse=True, batch_size=1000, limit=50)
        if email: mail.send(subject='Document Collection Test Run Complete', body=f"BRAINWORKS has finished a test run of document collection")
        return

    # normal run
    start = base.validate_date(start, format="%Y/%m/%d", throw=True)
    end = base.validate_date(end, format="%Y/%m/%d", throw=True) if end else None
    pm.generateTables()  # create tables if they don't already exist
    pm.bulk_collect(start, end_date=end, replace=replace, reverse=True)
    pm.insert_papers(replace=replace, reverse=True, batch_size=20000)

    if email:
        mail.send(subject='Document Collection Complete',
                  body=f"BRAINWORKS has finished running document collection.\nCollection Start Date: {start}\nCollection End Date: {end}\nTotal Time Taken: {cluster.format_seconds(time()-t0)}"
        )

@cli.command()
@email
@debug
@click.option('--test', "-t", is_flag=True, default=False, help="Runs on a very small dataset. Useful to check for problems before running with full data.")
@click.option('--replace', is_flag=True, default=False, help="Wipe and repopulate the citation table. This ensures all citation stats are up-to-date")
def icite(replace, test, email, debug):
    """ Collect citation statistics from iCite. Document collection must be run beforehand. """
    t0 = time()
    icite = iCite(config)

    if test:  # collect papers from a single day
        icite.db.query("SELECT now()")
        icite.log("Database connection successful.")
        icite.run(replace=replace, test=True)
        if email: mail.send(subject='Citation Stat Collection Test Run Complete', body=f"BRAINWORKS has finished a test run of the citation statistics collection")
        return

    # normal run
    icite.run(replace=replace)
    if email:
        mail.send(subject='Citation Stat Collection Complete',
                  body=f"BRAINWORKS has finished running citation statistics collection.\nTotal Time Taken: {mail.format_seconds(time()-t0)}"
        )

@cli.command()
@email
@debug
@click.option('--replace', is_flag=True, default=False, help="Wipe and repopulate the citation table. This ensures all citation stats are up-to-date")
def exporter(replace, email, debug):
    """ Collect all project data from ExPORTER """
    t0 = time()
    ex = Exporter(config)  # The exporter utility collects data from the NIH Exporter utility

    # normal run
    ex.run(replace=replace)  # create tables if they don't already exist
    if email:
        mail.send(subject='ExPORTER Collection Complete',
                  body=f"BRAINWORKS has finished running ExPORTER data collection.\nTotal Time Taken: {mail.format_seconds(time()-t0)}"
        )

@cli.command()
@email
@debug
@click.option('--test', is_flag=True, default=False, help="Extracts from a very small dataset. Useful to check for problems before running with full data.")
@click.option('--start', default="1980/01/01", help="The start date for extracting information from  publications. Format: YYYY/MM/DD")
@click.option('--end', help="The end date for pulling publications. Format: YYYY/MM/DD")
def extract(start, end, test, email, debug):
    """ Run the information extraction pipeline on the cluster (which must already be deployed and set up) """
    t0 = time()

    if test:  # collect papers from a single day
        start = date(year=2000, month=1, day=2)
        end = date(year=2000, month=1, day=2)

        # Run information extraction on cluster
        cluster.run_slurm(start, end, test)
        cluster.wait_for_slurm(10)
        if email: mail.send(subject='Information Extraction Test Run Complete', body=f"BRAINWORKS has finished a test run of information extraction")
        return

    start = base.validate_date(start, format="%Y/%m/%d", throw=True)
    end = base.validate_date(end, format="%Y/%m/%d", throw=True) if end else date.today()
    cluster.run_slurm(start, end, test)
    cluster.wait_for_slurm(30)

    if email:
        mail.send(subject='Information Extraction Test Run Complete',
                  body=f"BRAINWORKS has finished a test run of information extraction.\nExtraction Start Date: {start}\nExtraction End Date: {end}\nTotal Time Taken: {cluster.format_seconds(time()-t0)}"
        )


@cli.command()
@email
@debug
def transport_data(email, debug):
    """ Move all data from the Aurora database to the RedShift database """
    t0 = time()

    db = MySQLDatabase()
    rdb = RedShiftDatabase()

    # projects, abstracts
    tables = ["affiliations", "application_types", "citations", "citation_stats",
              "concepts", "documents", "grants", "id_map",
              "publications", "qualifiers", "topics", "triples", "link_tables"]

    db.dump_to_bucket(tables)
    rdb.load_from_bucket(tables)

    if email:
        mail.send(subject='Database Transfer Complete',
                  body=f"BRAINWORKS has finished the database transfer to RedShift.\nTotal Time Taken: {db.format_seconds(time()-t0)}"
        )

@cli.command()
@email
@debug
def create_website_tables(email, debug):
    """
    Create all pre-computed tables in RedShift, then transfer them to aurora.
    """
    t0 = time()
    pre = PreComputedTables(config)
    pre.UMLS()  # load UMLS tables from S3
    tables = pre.all()  # create pre-computed graph tables

    #rdb = RedShiftDatabase(config)
    #rdb.dump_to_bucket(tables)

    if email:
        mail.send(subject='Website Tables Created',
                  body=f"BRAINWORKS has finished creating the website tables.\nTotal Time Taken: {pre.format_seconds(time()-t0)}"
        )


@cli.command()
@email
@debug
def full_redshift_dump(email, debug):
    """ Dump all redshift tables to S3 """
    t0 = time()
    tables = ["affiliations", "application_types", "citations", "citation_stats",
              "concepts", "documents", "grants", "id_map", "concept_map", "definitions",
              "publications", "qualifiers", "topics", "triples", "link_tables"]

    rdb = RedShiftDatabase()
    rdb.dump_to_bucket(tables)

    if email:
        mail.send(subject='Full RedShift dump complete.',
                  body=f"BRAINWORKS has finished dumping all RedShift tables to the S3 bucket.\nTotal Time Taken: {rdb.format_seconds(time()-t0)}"
        )

@cli.command()
@email
@debug
@click.option('--test', is_flag=True, default=False, help="Runs the command on a very small dataset. Useful to check for problems before running with full data.")
@click.option('--start', help="The start date for pulling publications. Format: YYYY/MM/DD")
@click.option('--end', help="The end date for pulling publications. Format: YYYY/MM/DD")
@click.option('--replace', is_flag=True, default=False, help="Whether to wipe old collected data and re-populate")
def run(start, end, replace, email, test, debug):
    """
    Runs the full pipeline, including data collection, data processing, information extraction, and information processing.
    Specify the start and end dates for the pipeline to collect.
    """
    t0 = time()
    pm = PubmedCollector(config)  # collector
    icite = iCite(config)
    ex = Exporter(config)  # The exporter utility collects data from the NIH Exporter utility

    tables = ["affiliations", "application_types", "citations", "citation_stats",
              "concepts", "documents", "grants", "id_map", "link_tables",
              "publications", "qualifiers", "topics", "triples"]

    if test:  # collect papers from a single day
        start = pm.validate_date("2000/01/02", format="%Y/%m/%d", throw=True)
        end = pm.validate_date("2000/01/02", format="%Y/%m/%d", throw=True)

        pm.generateTables()  # create tables if they don't already exist
        pm.bulk_collect(start_date=start, end_date=end, replace=replace, reverse=True)
        pm.insert_papers(replace=replace, reverse=True, batch_size=1000, limit=50)

        icite.run(replace=replace, test=True)
        ex.run(replace=False)

        cluster.deploy(3)  # deploy cluster with 3 nodes
        cluster.wait_for_deploy()
        cluster.copy_to_cluster()    # copy repo to cluster
        cluster.setup_environ()      # setup python and whatnot
        cluster.run_slurm(start, end, test)
        cluster.wait_for_slurm(5)
        cluster.get_logs()  # retrieve logs first
        cluster.delete()

        db = MySQLDatabase()
        rdb = RedShiftDatabase()

        # transport from aurora to RedShift
        db.dump_to_bucket(tables)
        rdb.load_from_bucket(tables)

        # create pre-computed tables
        pre = PreComputedTables(config)
        tables = pre.all()

        cluster.wait_for_delete()

        if email: mail.send(subject='Full Test Run Complete', body=f"BRAINWORKS has finished a test run of the full pipeline.")
        return

    # normal run
    start = base.validate_date(start, format="%Y/%m/%d", throw=True)
    end = base.validate_date(end, format="%Y/%m/%d", throw=True) if end else None

    pm.generateTables()  # create tables if they don't already exist
    pm.bulk_collect(start, end_date=end, replace=replace, reverse=True)
    pm.insert_papers(replace=replace, reverse=True, batch_size=20000)

    icite.run(replace=replace)  # create tables if they don't already exist
    ex.run(replace=False)  # create tables if they don't already exist. Never replace the exporter stuff.

    cluster.deploy(cluster.max_nodes)  # deploy cluster with 100 nodes
    cluster.wait_for_deploy(10)
    cluster.copy_to_cluster()  # copy repo to cluster
    cluster.setup_environ()  # setup python and whatnot
    cluster.run_slurm(start, end, test)
    cluster.wait_for_slurm(30)
    cluster.get_logs()  # retrieve logs first
    cluster.delete()

    db = MySQLDatabase()
    rdb = RedShiftDatabase()

    # transport from aurora to RedShift
    db.dump_to_bucket(tables)
    rdb.load_from_bucket(tables)

    # create pre-computed tables
    pre = PreComputedTables(config)
    pre.all()

    if email:
        mail.send(subject='Full Run Complete',
                  body=f"BRAINWORKS has finished a full run.\nStart Date: {start}\nEnd Date: {end}\nTotal Time Taken: {cluster.format_seconds(time()-t0)}"
        )


@cli.command()
@email
@debug
def run_month(email, debug):
    """
    Runs the full pipeline for the last month, including data collection, data processing, information extraction, and information processing.
    """
    t0 = time()
    pm = PubmedCollector(config)  # collector
    icite = iCite(config)
    ex = Exporter(config)  # The exporter utility collects data from the NIH Exporter utility

    tables = ["affiliations", "application_types", "citations", "citation_stats",
              "concepts", "documents", "grants", "id_map", "link_tables",
              "publications", "qualifiers", "topics", "triples"]

    # normal run
    end = date.today()
    start = end - timedelta(days=31)

    pm.generateTables()  # create tables if they don't already exist
    pm.bulk_collect(start, end_date=end, replace=False, reverse=True)
    pm.insert_papers(replace=False, reverse=True, batch_size=20000)

    icite.run(replace=True)  # run iCite
    ex.run(replace=False)  # run exporter data

    cluster.deploy(cluster.max_nodes)  # deploy cluster with 100 nodes
    cluster.wait_for_deploy(10)
    cluster.copy_to_cluster()  # copy repo to cluster
    cluster.setup_environ()  # setup python and whatnot
    cluster.run_slurm(start, end)
    cluster.wait_for_slurm(60)
    cluster.get_logs()  # retrieve logs first
    cluster.delete()

    db = MySQLDatabase()
    rdb = RedShiftDatabase()

    # transport from aurora to RedShift
    db.dump_to_bucket(tables)
    rdb.load_from_bucket(tables)

    # create pre-computed tables
    pre = PreComputedTables(config)
    pre.all()

    if email:
        mail.send(subject='Full Run Complete',
                  body=f"BRAINWORKS has finished a full run.\nStart Date: {start}\nEnd Date: {end}\nTotal Time Taken: {cluster.format_seconds(time()-t0)}"
        )



##########################
# Cluster management commands
@cli.group("cluster")
def cluster_cli():
    """
    Control the Parallel Compute Cluster
    """
    pass

@cluster_cli.command()
@debug
@email
@click.argument("nodes", nargs=1, type=click.INT, required=False)
def deploy(nodes, email, debug):
    """ Deploy the cluster """
    try:
        t0 = time()

        cluster.deploy(nodes)
        cluster.log("This will take awhile (20-30 minutes)")
        cluster.wait_for_deploy(10)  # wait until fully deployed, check every 10 seconds
        cluster.copy_to_cluster()    # copy repo to cluster
        cluster.setup_environ()      # setup python and whatnot

        elapsed = cluster.format_seconds(time()-t0)
        if email: mail.send(subject="Cluster Successfully Deployed", body=f"The High-Performance Compute Cluster has been deployed.\nElapsed Time: {elapsed}")
    except Exception as e:
        if email: mail.send(subject="Cluster Failed to Deploy", body=f"The High-Performance Compute Cluster failed to deploy.\nError: {mail.trace()}")


@cluster_cli.command()
@debug
@email
def delete(debug, email):
    """ Delete the Cluster """
    try:
        t0 = time()

        cluster.log("This may take a few minutes")
        cluster.get_logs()  # retrieve logs first
        cluster.delete()
        cluster.wait_for_delete(10)  # wait for fully deleted, check every 10 seconds

        if email: mail.send(subject="Cluster Deleted", body=f"The High-Performance Compute Cluster has been successfully deleted.\nElapsed Time: {cluster.format_seconds(time()-t0)}")
    except Exception as e:
        if email: mail.send(subject="Cluster Failed to Delete", body=f"The High-Performance Compute Cluster failed to delete.\nError: {mail.trace()}")

@cluster_cli.command()
@debug
@email
def get_logs(debug, email):
    """ Retrieve logs from the cluster """
    cluster.get_logs()

@cluster_cli.command()
@debug
def status(debug):
    """ Get cluster status """
    cluster.log(cluster.status)

@cluster_cli.command()
@debug
def ssh(debug):
    """ Open an SSH terminal session to the cluster head node """
    cluster.ssh_to_cluster()

@cluster_cli.command()
@debug
def sync(debug):
    """ Copy repo to cluster """
    cluster.copy_to_cluster()    # copy repo to cluster


if __name__ == '__main__':
    cli()