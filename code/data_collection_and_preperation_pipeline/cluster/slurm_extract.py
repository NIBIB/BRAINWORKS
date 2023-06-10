import os
import sys
import inspect

"""
This script is to be run on each job in a SLURM cluster.
"""

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir  = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from utils.extraction.extraction import NLPExtractor
ex = NLPExtractor()
ID = int(os.environ.get("SLURM_ARRAY_TASK_ID", 0))
ex.extract_information(parallel_index=ID, db_insert=True, batch_size=1000, show_progress=True)

