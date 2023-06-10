import os
from os import environ
import sys
import datetime
import inspect
import subprocess

DUMPDIR = "/home/ubuntu/brainworks-public/data/dumps"

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir  = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from utils.database.database import database   # import the utility

db = database()  # database
now = datetime.datetime.now()

# Dump current database snapshot to file
if not os.path.exists(DUMPDIR):
    os.mkdir(DUMPDIR)

print("Dumping database to file...")
dump_file = f"{DUMPDIR}/{now.strftime('%Y-%m-%d')}_manual.sql"
process = subprocess.Popen(f"mysqldump --skip-add-drop-table --no-create-info --host={environ['DB_HOST']} --port={environ['DB_PORT']} --user={environ['DB_USER']} --password={environ['DB_PASSWORD']} brainworks > {dump_file}", shell=True)
process.wait()