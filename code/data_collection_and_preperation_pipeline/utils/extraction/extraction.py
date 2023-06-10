from datetime import datetime, timedelta, date
import time
import re
import os, ssl
import math
import pickle

if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

# To make sure the tokenizer doesn't work in parallel because it may cause multiprocessing deadlocks.
os.environ["TOKENIZERS_PARALLELISM"] = "false"
           

import stanza
import spacy
import spacy_transformers
from   scispacy.abbreviation import AbbreviationDetector
from   scispacy.linking import EntityLinker
from   stanza.server import CoreNLPClient
import logging

from utils.database.database import MySQLDatabase
from utils.base import Base, ThreadQueue


class NLPExtractor(Base):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logging.getLogger('allennlp.common.params').disabled = True 
        logging.getLogger('allennlp.nn.initializers').disabled = True 
        logging.getLogger('allennlp.modules.token_embedders.embedding').setLevel(logging.INFO) 
        logging.getLogger('urllib3.connectionpool').disabled = True

        self.db = MySQLDatabase()

        # the number of nodes deployed
        self.nodes = int(os.popen("sinfo --Node | wc -l").read()) - 1

        self.pmid_split_directory = "cluster/assigned_slurm_pmids"
        if not os.path.exists(self.pmid_split_directory):
            os.mkdir(self.pmid_split_directory)

        self.generateTables()
        self.spacy_models = {}
        self.abbr_model = None
        
        # The CoreNLP Java client
        self.client = None
        self.memory_threshold = 90  # client restart memory percent threshold
        self.threads = os.cpu_count()  # threads equal to number of CPUs

        # Column names to insert into tables
        self.triple_cols = ['pmid', 'triple_id','pub_date','subject','relation','object','confidence','sentence_number','start_char','end_char']
        self.concept_cols = ['pmid', 'triple_id','concept_type','concept_id','concept_name','total_concepts','start_char','end_char','frag_start_char','frag_end_char']

    def generate_paper_split(self, start_date, end_date, replace=False, benchmark=False):
        """
        Get an even spread of PMIDs for <num> parallel jobs to process.
        Write to disk a file for each parallel job containing a pickled list of PMIDs.
        Should be called once BEFORE extraction is deployed to a parallel cluster.
        Then in each parallel job, call self.get_assigned_papers(index), where index is 0 to num-1

        <num> number of parallel jobs to split papers among
        <replace> whether to include papers already in the triples table
        <start_date>, <end_date> datetime objects
        <benchmark> For benchmarking only. Generate the exact same subset of 1000 papers for each job.
        """
        start_date_string = self.date_string(start_date)
        end_date_string = self.date_string(end_date)

        self.log(f"Generating even paper split for parallel jobs... ")
        self.log(f"Replacement: {replace}")

        self.log(f"Date Range: {start_date_string} - {end_date_string}")
        self.log(f"Parallel Jobs: {self.nodes:,}")

        assert self.nodes >= 1, "Number of jobs must be at least 1."

        # get all pmids
        self.log("Querying for PMIDs in database...")
        self.mark_time('query')

        if replace:  # get all pmids in documents table
            query = f"""
            SELECT DISTINCT d.pmid FROM documents d
            WHERE d.pub_date >= '{start_date_string}' AND d.pub_date <= '{end_date_string}'
            """
        else:  # get only PMIDs that aren't in the triples table
            query = f"""
                SELECT DISTINCT d.pmid FROM documents d
                LEFT JOIN triples t ON d.pmid = t.pmid
                WHERE t.pmid is NULL
                AND d.pub_date >= '{start_date_string}' AND d.pub_date <= '{end_date_string}'
            """
        result = self.db.query(query)
        if not result:
            self.log("No papers found in database. Database error?")
            return
        pmids = [row['pmid'] for row in result]
        self.add_time('query')
        self.log(f"PMIDs found in database: {len(pmids):,} ({self.get_time_total('query')})")
        self.clear_time('query')

        self.debug("Removing anything already in the data split directory...")
        for f in os.listdir(self.pmid_split_directory):
            os.remove(os.path.join(self.pmid_split_directory, f))

        # when benchmarking, give the same 1000 papers to each node (or less if less found)
        if benchmark:
            papers_per_job = min(1000, len(result))
            self.log(f"WARNING: Benchmarking {papers_per_job:,} papers")
            self.log(f"Writing paper split to disk.... ({self.pmid_split_directory})")
            pmids = [row['pmid'] for row in result[:papers_per_job]]  # same papers for each job
            for i in range(self.nodes):
                file = f"{self.pmid_split_directory}/{i}.pickle"
                with open(file, 'wb') as f:
                    pickle.dump(pmids, f, protocol=pickle.HIGHEST_PROTOCOL)
            return

        # Create files containing even splits of pmids
        pmids = list(pmids)
        num_papers = len(pmids)
        papers_per_job = int(math.ceil(num_papers / self.nodes))
        self.log(f"Total Papers: {num_papers:,}")
        self.log(f"Papers per Job: {papers_per_job:,}")
        self.log(f"Writing paper split to disk.... ({self.pmid_split_directory})")
        for i in range(self.nodes):
            start = i * papers_per_job  # start of slice
            end = start + papers_per_job  # end of slice
            pmids = [row['pmid'] for row in result[start:end]]
            file = f"{self.pmid_split_directory}/{i}.pickle"
            with open(file, 'wb') as f:
                pickle.dump(pmids, f, protocol=pickle.HIGHEST_PROTOCOL)

    def get_assigned_papers(self, index):
        """
        Given a parallel job index, retrieve the assigned PMIDs from disk, generated by self.generate_paper_split().
        Should be called within a parallel job.
        <index> should be from 0 to (number of jobs)-1
        """
        self.debug("Retrieving assigned PMIDs for this job...")
        file = f"{self.pmid_split_directory}/{index}.pickle"
        if os.path.exists(file):
            with open(file, 'rb') as f:
                return pickle.load(f)
        else:
            self.log(
                f"\nCould not find file with assigned PMIDs: {file}\nNLPExtractor.generate_paper_split() must be called before NLPExtractor.get_assigned_papers()")
            return []

    def run_slurm(self):
        """
        Generate the Slurm script to run, then run it.
        """
        script = f"""#!/bin/bash
#SBATCH  --output=cluster/output/out/slurm-%A-%a.out
#SBATCH  --error=cluster/output/err/error-%A-%a.err
#SBATCH  --array=0-{self.nodes-1}
#SBATCH  --nodes=1
#SBATCH  --exclusive
#SBATCH  --partition=q1

module refresh
module load use.own
module load java/jdk-17.0.1
echo "SLURM_JOB_ID:        $SLURM_JOB_ID"
echo "SLURM_ARRAY_JOB_ID:  $SLURM_ARRAY_JOB_ID"
echo "SLURM_ARRAY_TASK_ID: $SLURM_ARRAY_TASK_ID"
echo "SLURM_ARRAY_TASK_COUNT: $SLURM_ARRAY_TASK_COUNT"

source venv/bin/activate
python3 -c '
import os
from utils.extraction.extraction import NLPExtractor
from configuration.config import Config
config = Config()
config.debug = {self.config.debug}
ex = NLPExtractor(config)
ID = int(os.environ.get("SLURM_ARRAY_TASK_ID", 0))
ex.extract_information(parallel_index=ID, db_insert=True, batch_size=1000, show_progress=True)
';
"""
        with open("cluster/run_slurm.sh", "w") as file:
            file.write(script)

        self.log("Generated SLURM script. Dispatching SLURM jobs.")
        self.log(os.popen("sbatch cluster/run_slurm.sh").read())
        time.sleep(1)  # just to give popen time to close

    def check_client(self, restart=True):
        """
        Initializes the client if it isn't already.
        Checks the memory usage of the CoreNLP client.
        When memory usage gets too high, the client is restarted.
        """
        if not self.client:
            self.log('Initializing CoreNLP Client... ')
            self.client = CoreNLPClient(
                timeout=60000,
                be_quiet=True,
                #preload=True,  # doesn't seem to work :(
                threads=self.threads,
                start_server=stanza.server.StartServer.TRY_START,  # start new server or connect to a pre-existing one if it already exists (allows multiple threads)
                properties=self.config.CoreNLP_properties,
                memory=self.config.CoreNLP_memory,
                endpoint=self.config.CoreNLP_endpoint,
            )
        elif restart and self.memory(num=True) > self.memory_threshold:  # if memory over threshold
            self.log(f"Restarting CoreNLP Server (memory > {self.memory_threshold}%)")
            self.client.stop()
            self.client.start()

    def initialize_entity_resources(self):
        """ Download Spacy models and make sure they are in the memory before continuing """
        if len(self.spacy_models): return  # already done
        self.log('Initializing Spacy Entity Extraction Model...')
        self.spacy_models = {}
        for model in self.config.ner_models:  # for each model in config
            # Load the model from an external resource unless already in cache.
            # Exclude all pipes except the NER
            self.spacy_models[model] = spacy.load(model, exclude=['tok2vec', 'tagger', 'parser', 'attribute_ruler', 'lemmatizer', 'transformer'])
            self.log("Spacy Pipes loaded: ", self.spacy_models[model].pipe_names)

        for model in self.config.ner_models:  # for each model again

            # prevent tensor size mismatch error: https://github.com/explosion/spaCy/issues/7891#issuecomment-1218095552
            # self.spacy_models[model].get_pipe("transformer").model.tokenizer.model_max_length = 512

            self.log("Waiting for model to download: ", model)
            loaded = False
            while not loaded:  # loop until this resource is loaded
                self.log("Attempting to add pipe...")
                try:  # attempt to add Scispacy pipe. Will throw an error if the resource isn't loaded yet.
                    self.spacy_models[model].add_pipe("scispacy_linker", config={
                        "resolve_abbreviations": True,
                        "linker_name": "umls",
                        #"threshold": 0.5,
                        #"filter_for_definitions": False,
                        #"no_definition_threshold": 0.5,
                    })
                    self.log("Pipe added!")
                    loaded = True
                except Exception as e:
                    self.log("Resource not ready.")
                    self.debug(self.trace())
                    time.sleep(1)  # wait a sec before trying again

    def generateTables(self):
        query = """CREATE TABLE IF NOT EXISTS `triples` (
                  `pmid`            int(11) unsigned    NOT NULL     COMMENT 'The PubMed identification number.',
                  `triple_id`       int                 NOT NULL     COMMENT 'ID for each triple. Unique for each PMID',
                  `pub_date`        date                DEFAULT NULL COMMENT 'The full date on which the issue of the journal was published.',
                  `subject`         varchar(200)        NOT NULL     COMMENT 'The subject of the sentence.',
                  `relation`        varchar(200)        NOT NULL     COMMENT 'The relationship between the subject and the objec.',
                  `object`          varchar(200)        NOT NULL     COMMENT 'The object of the sentence.',
                  `confidence`      int                 DEFAULT NULL COMMENT 'The confidence of the extraction',
                  `sentence_number` int                 DEFAULT NULL COMMENT 'The sentence that this showed up in.',
                  `start_char` int                      NOT NULL     COMMENT 'Starting character of the sentence containing this triple',
                  `end_char`   int                      NOT NULL     COMMENT 'Ending character of the sentence containing this triple',
                  PRIMARY KEY (`pmid`, `triple_id`),
                  KEY          `pmid_index`         (`pmid`),
                  KEY          `pub_date_index`     (`pub_date`),
                  KEY          `confidence_index`   (`confidence`),
                  KEY          `sentence_number`    (`sentence_number`),
                  FULLTEXT KEY `subject_index`      (`subject`),
                  FULLTEXT KEY `object_index`       (`relation`),
                  FULLTEXT KEY `relation_index`     (`object`),
                  KEY          `start_char_index`               (`start_char`),
                  KEY          `end_char_index`                 (`end_char`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
        
        self.db.query(query)

        query = """CREATE TABLE IF NOT EXISTS `concepts` (
                  `id`                   bigint(20) unsigned NOT NULL      AUTO_INCREMENT,
                  `pmid`                 int(11)             NOT NULL      COMMENT 'The PubMed identification number.',
                  `triple_id`            int unsigned        NOT NULL      COMMENT 'The triple ID this concept belongs to for this PMID',
                  `concept_type`         varchar(12)         NOT NULL      COMMENT 'e.g. subject, object, relation',
                  `concept_id`           varchar(20)         NOT NULL      COMMENT 'The UMLS Concept CUI',
                  `concept_name`         varchar(100)        NOT NULL      COMMENT 'The subject name',
                  `total_concepts`       int                 NOT NULL      COMMENT 'The total number of concepts for this triple hash',
                  `start_char`           int                 NOT NULL      COMMENT 'Starting character relative to the start of the sentence',
                  `end_char`             int                 NOT NULL      COMMENT 'Ending character relative to the start of the sentence',
                  `frag_start_char`      int                 NOT NULL      COMMENT 'Starting character relative to the triple fragment text',
                  `frag_end_char`        int                 NOT NULL      COMMENT 'Ending character relative to the triple fragment text',
                  PRIMARY KEY (`id`),
                  KEY `entities_triple_index`          (`pmid`, `triple_id`),
                  KEY `entities_conceptid_index`       (`concept_id`),
                  KEY `entities_conceptname_index`     (`concept_name`),
                  KEY `entities_concepttypename_index` (`concept_type`,`concept_name`),
                  KEY `entities_conceptnumber_index`   (`total_concepts`)
                ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4"""
        self.db.query(query)

    def get_optimal_jobs(self, start_date, max_papers=5000):
        """ Return the number of parallel SLURM jobs necessary to achieve the given max papers per job """
        date_string = self.date_string(start_date)
        data = self.db.query(f"""
            SELECT COUNT(DISTINCT pmid) as cnt FROM documents
            WHERE content_type  = 'abstract'
            AND content IS NOT NULL
            AND pub_date > "{date_string}"
        """)
        total_papers = int(data[0]["cnt"])

        # Ensure enough jobs to give a maximum of max_papers papers per job
        total_nodes = int(os.environ.get('CLUSTER_NODES'))  # total nodes available in cluster
        min_jobs = int(math.ceil(total_papers / max_papers))  # minimum number of jobs for this max number of papers per job

        # How many jobs to schedule.
        # Either the minimum number above, or the number of available nodes (if higher).
        total_jobs = max(min_jobs, total_nodes)

        self.log(f"Start Date: {date_string}")
        self.log(f"Total documents: {total_papers}")
        self.log(f"Total nodes: {total_nodes}")
        self.log(f"Total jobs: {total_jobs}")
        self.log(f"documents/job: {int(total_papers / total_jobs)}")

    def extract_information(self, pmids=None, parallel_index=None, db_insert=True, batch_size=1000, show_progress=True):
        """
        Extract triples and concepts from a given list of PMIDs, or if not provided,
            use parallel_index to get a list of assigned PMIDs generated by self.generate_paper_split()

        <pmids> list of PMIDs
        <parallel_index> must be a unique index from 0 to (total jobs)-1 for each parallel job running this function.
        """
        assert pmids is not None or parallel_index is not None, "Either a list of pmids or a parallel index must be given"

        if pmids is None:  # using parallel mode
            self.log("Running information extraction in parallel jobs.")
            assert parallel_index is not None, "parallel_index not provided."
            pmids = self.get_assigned_papers(parallel_index)  # get pmids assigned to this job index
            self.log(f"Got {len(pmids):,} PMIDs assigned to this job")
            if not pmids: return
        else:
            self.log("Running information extraction from a list of PMIDs (not in parallel).")

        # list of lists of values to be inserted into each table.
        # Must match column order of self.triple_cols and self.concept_cols
        triple_params = []  # list of lists of values
        concept_params = []  # list of lists of values

        total_papers = len(pmids)  # total number of papers
        pmid_batches = self.batch_list(pmids, size=batch_size)  # batch PMIDs according to batch size

        total_batches = len(pmid_batches)  # total number of batches

        self.initialize_entity_resources()  # download entity resources if not already (slow but happens once)
        self.check_client()  # start CoreNLP client

        # logging
        self.log("Beginning Extraction...")
        self.log(f"Annotation Threads: {self.threads}")
        if show_progress:
            self.log(f"\nPapers to extract: {total_papers:,} (with batch size {batch_size:,})")
            self.log("Complete | Total Time || Success | Batch Time || Query |  NER   | Stanza | Triples | Insert || Memory Usage")
            self.debug("   PMID   | Length | Time |  NER  | Stanza | Triples | Memory Usage")
            self.log("----------------------------------------------------------------------------------------------------------------------")

        # tracking stats
        total_success = 0  # successful papers
        batch_success = 0  # successful papers in a batch
        total_errors = 0  # has any kind of error
        total_no_triples = 0  # no triples were found
        total_no_content = 0  # no content associated with the paper (and thus no triples)
        total_triples = 0  # total triples found
        total_entities = 0  # total entities found

        insert_threads = []  # async results for threaded inserts
        queue = ThreadQueue(self.threads)  # create new thread queue for the CoreNLP annotations

        self.mark_time('total')  # total time passed
        for b, pmids in enumerate(pmid_batches):  # for each PMID batch
            self.mark_time('batch')

            self.mark_time("query")
            papers = self.get_papers_from_pmids(pmids)  # list of dicts with keys "pmid", "pub_date", and "content"
            self.add_time('query')

            # submit each paper to the queue for annotation
            self.debug("Submitting batch to annotation queue")
            for paper in papers:
                pmid = paper['pmid']
                pub_date = paper['pub_date']
                content = paper['content']  # abstract

                # skip papers with no content
                if not content:
                    total_no_content += 1
                    continue

                # submit paper to thread queue
                queue.submit(self.annotate, [pmid, pub_date, content])

            # go through each document from the annotation queue
            for _ in range(len(papers)):
                self.mark_time('paper')

                self.mark_time("stanza")
                paper = queue.next()  # get next available document
                self.add_time('stanza')

                if paper is None:  # queue empty - batch finished
                    break

                pmid = paper['pmid']
                pub_date = paper['pub_date']
                content = paper['content']
                document = paper['document']  # Stanza document object

                if not document:
                    total_errors += 1
                    self.debug(f"CoreNLP failed to annotate content.")
                    continue

                self.mark_time('ner')
                entities = self.get_entities(content)  # Extract the entities, indexed by start_char
                if not len(entities):
                    self.err(f"No entities found for PMID: {pmid}")
                else:
                    total_entities += len(entities)
                self.add_time('ner')

                self.mark_time('triples')
                try:
                    triples = []
                    triples = self.get_triples(document, entities)  # match triples to entities and filter
                    total_triples += len(triples)
                except Exception as e:
                    total_errors += 1
                    self.err(f"Failed to get triples from annotated document from PMID: {pmid}. {self.trace()}")
                    continue

                self.debug(f"Triples: {len(triples)} | Entities: {len(entities)}")

                if not triples:
                    total_no_triples += 1
                    self.err(f"No triples extracted for PMID: {pmid}")
                    continue

                try:  # construct database inserts
                    paper_triple_params, paper_concept_params = [], []
                    paper_triple_params, paper_concept_params = self.construct_rows(triples, pmid, pub_date)
                except Exception as e:
                    total_errors += 1
                    self.err(f"Failed to construct rows for PMID: {pmid}. {self.trace()}")
                    continue
                self.add_time('triples')

                # success!
                triple_params += paper_triple_params
                concept_params += paper_concept_params
                total_success += 1
                batch_success += 1

                self.add_time('paper')

                # debug logging
                if self.config.debug:  # print for each paper in debug mode
                    last_paper = self.get_time_last('paper', 2)  # last paper time
                    last_ner = self.get_time_last('ner', 3)  # last ner time
                    last_stanza = self.get_time_last('stanza', 3)  # last stanza time
                    last_triples = self.get_time_last('triples', 4)  # last triples time
                    self.debug(f"{pmid:8} | {len(content):6} | {last_paper:4} | {last_ner:5} | {last_stanza:6} | {last_triples:8} | {self.memory()}\n")

            # Batch finished!

            self.mark_time('insert')
            for result in insert_threads:  # wait for previous batch inserts to finish if they haven't already
                result.wait()
            # Insert batch into Triples and Concepts tables
            r1 = self.db.insert_row('triples', self.triple_cols, triple_params, db_insert=db_insert, threaded=True)
            r2 = self.db.insert_row('concepts', self.concept_cols, concept_params, db_insert=db_insert, threaded=True)
            self.add_time('insert')

            triple_params, concept_params, insert_threads = [], [], []  # reset insert values for next batch
            if r1: insert_threads.append(r1)  # threads to wait on before next insert
            if r2: insert_threads.append(r2)

            self.add_time('batch')

            # show progress after batch
            progress = self.progress(b, total_batches, every=1)
            if show_progress and progress:
                total = self.get_time_total('total', 0)  # total time passed
                batch = self.get_time_last('batch', 2)  # last batch time
                query = self.get_time_last('query', 2)  # paper query time for the batch
                insert = self.get_time_last('insert', 2)  # insert time for the batch

                ner = self.get_time_sum('ner', 2)  # summed ner time
                _stanza = self.get_time_sum('stanza', 2)  # summed stanza time
                triples = self.get_time_sum('triples', 2)  # summed triples time

                self.log(f"{progress:8} | {total:10} || {batch_success:7,} | {batch:10} || {query:5} | {ner:7} | {_stanza:6} | {triples:9} | {insert:6} || {self.memory()}")

                self.clear_time('ner', 'stanza', 'triples')
                batch_success = 0  # reset number of successful papers in the batch

        # All batches finished!

        # wait for the final insert
        for result in insert_threads:
            result.wait()

        # show some stats
        success_percent = round(100*total_success/total_papers,3) if total_papers else 0
        error_percent = round(100*total_errors/total_papers,3) if total_papers else 0
        no_triples_percent = round(100*total_no_triples/total_papers,3) if total_papers else 0
        no_content_percent = round(100*total_no_content/total_papers,3) if total_papers else 0
        avg_triples = round(total_triples/total_success,1) if total_success else 0
        avg_entities = round(total_entities/total_success,1) if total_success else 0

        self.log(f"Extraction Complete ({self.get_time_total('total')})")
        self.log(f"Succeeded: {total_success:,} ({success_percent}%)")
        self.log(f"Errors: {total_errors:,} ({error_percent}%)")
        self.log(f"No Triples: {total_no_triples:,} ({no_triples_percent}%)")
        self.log(f"No Content: {total_no_content:,} ({no_content_percent}%)")
        self.log()
        self.log(f"Total Triples: {total_triples:,}  (Avg/paper: {avg_triples})")
        self.log(f"Total Entities: {total_entities:,}   (Avg/paper: {avg_entities}")

    def get_papers_from_pmids(self, pmids):
        """
        Retrieve a list of rows for papers in the database in the given list of PMIDs.
        Each returned row has keys "pmid", "pub_date", and "content".
        """
        pmids = [str(pmid) for pmid in pmids]  # make sure they are all strings
        result = self.db.query(f"""
            SELECT pmid, MAX(pub_date) as pub_date, content
            FROM documents 
            WHERE content_type = "abstract" 
            AND pmid IN ({", ".join(pmids)})
            GROUP BY pmid
        """)
        if result is None:
            self.log("No papers found. Database error?")
            return []
        return result

    def lemmatize(self, text):
        """ Unused """
        nlp = stanza.Pipeline(lang='en', processors="tokenize, lemma", verbose=False)
        en_doc = nlp(text)
        tokenized = []
        for i, sent in enumerate(en_doc.sentences):
            for j, token in enumerate(sent.words):
                tokenized.append(token.lemma)

        return ' '.join(tokenized)

    def unAbbreviate(self, text):
        """ Unused """
        self.log('Initializing Abbreviation Model...')

        if self.abbr_model is None:
            self.abbr_model = spacy.load(self.config.abbreviation_model)
            self.abbr_model.add_pipe("abbreviation_detector")

        doc = self.abbr_model(text)
        replace = {}
        for abrv in doc._.abbreviations:
            # Replace the first instance of the abbreviation
            text = re.sub(f'\([ ]*{str(abrv)}[ ]*\)', '', text)

            # unabbreviate each instance
            replace[str(abrv)] = str(abrv._.long_form)
        return text.replace(str(abrv), str(abrv._.long_form))

    def annotate(self, pmid, pub_date, text):
        """ Submit a given document to be annotated by the CoreNLP client """
        self.check_client()  # initialize/restart client if necessary
        self.debug(f"submitting {pmid} to client...")

        # return this
        data = {
            'pmid': pmid,
            'pub_date': pub_date,
            'content': text,
            'document': None,  # Stanza document object
        }

        try:  # Run the Information Extraction Client.
            data['document'] = self.client.annotate(text)
        except stanza.server.client.TimeoutException:
            self.log(f"Stanza CoreNLP server timed out on PMID: {pmid}")
        except stanza.server.client.AnnotationException as e:
            self.log(f"Stanza CoreNLP server error on PMID: {pmid}")
            self.log(f"{e.__class__.__name__} {e}")

        return data

    def get_tree_triples(self, text):
        """
        Searches the given text constituency parse tree with the given TRregEx pattern.
        Returns the matched triples in the same form as OpenIE.
        """
        self.debug("TREE TRIPLES")
        pattern = "S < NP=subject < (VP=verb << (NP=object !>> NP))"
        matches = self.client.tregex(text, pattern)
        triples = []
        for i, sentence in enumerate(matches['sentences']):
            for j, match in sentence.items():
                start = sentence.get('characterOffsetBegin')
                end = sentence.get('characterOffsetEnd')
                sentence_number = i
                named = match['namedNodes']

                # get named variables from the tregex pattern match
                variables = {}
                for dic in named:
                    name = list(dic.keys())[0]
                    props = dic[name]
                    variables[name] = props['spanString']

                subject = variables['subject']
                object = variables['object']
                relation = variables['verb'].replace(object, '')  # remove the object from the verb

                triple = {'subject': subject,
                          'relation': relation,
                          'object': object,
                          'sentence_number': sentence_number,
                          'start_char': start,  # full sentence start and end characters
                          'end_char': end,
                          }
                triples.append(triple)
                self.log(f"{subject} | {relation} | {object}")
        return triples

    def get_triples(self, document, entities):
        """ Extract triples and associated entities from the given document """
        # get OpenIE triples
        triples = []
        for i, sentence in enumerate(document.sentence):
            for triple in sentence.openieTriple:
                triples.append({
                    'subject': triple.subject,
                    'relation': triple.relation,
                    'object': triple.object,
                    'confidence': triple.confidence,
                    'sentence_number': i,
                    'start_char': sentence.characterOffsetBegin,
                    'end_char': sentence.characterOffsetEnd,
                    'subject_entities': self.tokens_to_entities(triple.subjectTokens, sentence, entities),
                    'relation_entities': self.tokens_to_entities(triple.relationTokens, sentence, entities),
                    'object_entities': self.tokens_to_entities(triple.objectTokens, sentence, entities),
                })

        #triples += self.get_tree_triples(text)
        triples = self.filter_triples(triples)  # filter for only the best triples
        return triples

    def filter_triples(self, triples):
        """ Extracting triples from a given paper """
        # only take triples that have subject and object entities
        triples = [t for t in triples if t.get('subject_entities') and t.get('object_entities')]

        def sort_by(triple):
            return (
                triple['sentence_number'],  # first sort by sentence number ascending
                -(len(triple['subject_entities']) + len(triple['object_entities'])),
                # then sort by number of subject+object entities descending
                -(len(triple['subject']) + len(triple['object'])),
                # then sort by total length of the subject+object descending
                -len(triple['relation_entities']),  # sort by number of relations descending
                -len(triple['relation'])  # sort by length of relation descending
            )

        triples = sorted(triples, key=sort_by)

        sentence_num = -1
        keep_triples = []
        completed = []
        for triple in triples:
            # The goal here is to trim down things that occur within a given sentence.
            if sentence_num != triple['sentence_number']:
                sentence_num = triple['sentence_number']
                completed = []
                # self.debug()
                # self.debug(sentence_num)

            subjects = set([e['entity']['id'] for e in triple['subject_entities']])
            objects = set([e['entity']['id'] for e in triple['object_entities']])

            keep = True
            for pair in completed:
                # if both subject and object entities are a subset of any previous subject and object entities
                if subjects.issubset(pair['subjects']) and objects.issubset(pair['objects']):
                    keep = False
                    break
                # if the subject + object entities are completely contained within either the subject or object of another triple
                all = subjects.union(objects)
                if all.issubset(pair['subjects']) or all.issubset(pair['objects']):
                    keep = False
                    break

            # self.debug(f"{'X' if keep else ' '} | {'T' if triple.get('confidence') is None else ' '} | {triple['subject']} | {triple['relation']} | {triple['object']} < {len(triple['subject_entities'])} | {len(triple['relation_entities'])} | {len(triple['object_entities'])}")

            if keep:
                completed.append({'subjects': subjects, 'objects': objects})
                keep_triples.append(triple)

        return keep_triples

    def get_entities(self, text):
        """
        Construct a dictionary of entities found in the text.
        Keys are the starting character position of each entity.
        Returns an index of entities, where keys are the start_char of the entity.
        """

        entities = {}
        # Get the set of entities using the model
        for model in self.config.ner_models:
            try:
                bio_doc = self.spacy_models[model](text)
                linker = self.spacy_models[model].get_pipe("scispacy_linker")

                same = 0
                tot = 0
                for entity in bio_doc.ents:
                    # Loop through all potential CUI matches for this entity
                    potentials = entity._.kb_ents  # potential UMLS matches
                    if not len(potentials): continue

                    best_match_cui = potentials[0][0]  # first one is the most confident match (CUI, confidence)
                    e = linker.kb.cui_to_entity[best_match_cui]  # convert CUI to entity
                    tot += 1
                    if entities.get(entity.start_char): same += 1
                    entities[entity.start_char] = {
                        'id': e.concept_id,
                        'name': e.canonical_name,
                        'start_char': entity.start_char,
                        'end_char': entity.end_char,
                        #'aliases': e.aliases,
                        #'definition': e.definition,
                        #'types': e.types,
                    }

                self.debug(f"NER Model: {model}, total: {tot}, dupes: {same}")

            except Exception as e:
                self.err(f"Error running NER model '{model}': {self.trace()}")
                continue

        return entities

    def tokens_to_entities(self, triple_tokens, sentence, entities):
        """
        Returns entity positional information about a given triple fragment.
        <triple_tokens> A list of tokens found in that triple
        <sentence> The sentence Object containing this triple.
        <entities> A dictionary of entities, where keys are the starting character of that entity

        Returns list of token dictionaries
            start_char and end_char: position relative to start of the sentence
            frag_start_char and frag_end_char: positions relative to the start of the triple fragment
            text: original text of the token
            entity: Named entity associated with this token (or empty)

        Note that the position of each token relative to the SENTENCE is different than the positions relative to the FRAGMENT.
        The sentence is the original text from the document, while the triple fragment can be lemmatized and have the tokens in a different order.
        """
        tokens = []
        pos = 0  # keep track of current position in fragment
        for token in triple_tokens:  # for each token in this triple fragment

            # triple token index gives us the token object from the full sentence, which has the information we want
            t = sentence.token[token.tokenIndex]

            if entities.get(t.beginChar):  # if there are entities associated
                tokens.append({
                    'start_char': t.beginChar - sentence.characterOffsetBegin,  # relative to start of sentence
                    'end_char': t.endChar - sentence.characterOffsetBegin,  # relative to start of sentence
                    'frag_start_char': pos,
                    'frag_end_char': pos + len(t.originalText),
                    'text': t.originalText,
                    'word': t.word,
                    'value': t.value,
                    'entity': entities.get(t.beginChar, '')  # get the Spacy entity that occurred at this location
                })

            pos += len(t.originalText) + 1  # increment position by token size +1 for whitespace
        return tokens

    def construct_rows(self, triples, pmid, pub_date):
        """
        Given the extracted triples from a paper, returns the columns to be inserted into the Triples and Concepts table.
        """
        triple_params = []
        concept_params = []

        # Extract the triplets

        triple_ID = 0  # unique ID for triples in this PMID

        # Construct the parameters from the triplets
        for triple in triples:
            # Extract the confidence measure for the triple.
            confidence = None
            if triple.get('confidence'):
                confidence = int(100 * triple['confidence'])

            # Store the triple
            triple_params.append(
                [pmid, triple_ID, pub_date, triple['subject'], triple['relation'], triple['object'], confidence,
                 triple['sentence_number'], triple['start_char'], triple['end_char']])

            # Store the concepts
            for token in triple['object_entities']:
                e = token['entity']
                concept_params.append(
                    [pmid, triple_ID, 'object', e['id'], e['name'], len(triple['object_entities']), token['start_char'],
                     token['end_char'], token['frag_start_char'], token['frag_end_char']])

            for token in triple['subject_entities']:
                e = token['entity']
                concept_params.append([pmid, triple_ID, 'subject', e['id'], e['name'], len(triple['subject_entities']),
                                       token['start_char'], token['end_char'], token['frag_start_char'],
                                       token['frag_end_char']])

            for token in triple['relation_entities']:
                e = token['entity']
                concept_params.append(
                    [pmid, triple_ID, 'relation', e['id'], e['name'], len(triple['relation_entities']),
                     token['start_char'], token['end_char'], token['frag_start_char'], token['frag_end_char']])

            triple_ID += 1
        return triple_params, concept_params
