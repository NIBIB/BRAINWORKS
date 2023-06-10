from utils.database.database import MySQLDatabase
from utils.base import Base, ThreadQueue
import requests


class iCite(Base):
    """
    Uses the NIH iCite API to retrieve information in individual papers.

    API: https://icite.od.nih.gov/api
    Definitions and Calculatinos: https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.1002541
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://icite.od.nih.gov/api"

        # AsyncResult to wait on for database inserts
        self.database_insert = None

        # All database columns. These also correspond to the iCite API response data keys
        self.columns = ['pmid', 'relative_citation_ratio', 'nih_percentile', 'apt', 'citation_count', 'citations_per_year', 'field_citation_rate']
        self.table_name = "citation_stats"

        self.db = MySQLDatabase()

    def run(self, replace=True, test=False):
        """ Add the table and populate it """
        self.log("-----------------------------")
        self.log("Beginning iCite collection...")
        self.log(f"Replacement: {replace}")

        if replace:
            self.log("Dropping citation stats tables...")
            self.db.query(f"DROP TABLE IF EXISTS `{self.table_name}`")
        self.create_table()

        pmids = self.get_pmids_in_database(replace, test)
        if not len(pmids):
            self.log(f"iCite cannot populate database. No PMIDs found in documents table that weren't already in the {self.table_name} table")
            return

        self.collect(pmids)

    def create_table(self):
        """ Destroyes and re-creates the citation data table """
        self.log("Creating Citation Stats table if not exists...")
        query = f"""
        CREATE TABLE IF NOT EXISTS `{self.table_name}` (
            `pmid`                      int(11)         NOT NULL        COMMENT 'The PubMed identification number.',
            `relative_citation_ratio`   float           DEFAULT NULL    COMMENT 'Relative citation ratio',
            `nih_percentile`            float           DEFAULT NULL    COMMENT 'NIH percentile impact score (lower is better)',
            `apt`                       float           DEFAULT NULL    COMMENT 'Approximate Potential to Translate. Liklihood to be later cited by clinical trials.',
            `citation_count`            int             DEFAULT NULL    COMMENT 'Number of citations',
            `citations_per_year`        float           DEFAULT NULL    COMMENT 'Average citations per year',
            `field_citation_rate`       float           DEFAULT NULL    COMMENT 'Field Citation Rate: Average Journal Citation Rate in a given co-citation network.',
            
            PRIMARY KEY (`pmid`),
            UNIQUE KEY   `pmid`     (`pmid`)
            
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        self.db.query(query)

    def insert(self, rows):
        """
        Insert rows into the database.
        <rows> should be a list of lists of items for their respective column.
        """
        if not len(rows): return  # nothing to insert
        assert len(rows[0]) == len(self.columns), "Length of rows to insert do not match length of columns."
        # construct values in this row for the INSERT statement
        row_values = []
        for row in rows:
            row = [str(x) if x is not None else "NULL" for x in row]
            row_values.append(f"({', '.join(row)})")

        query = f"""
        INSERT IGNORE `citation_stats` ({', '.join(self.columns)})
        VALUES {', '.join(row_values)}
        """
        if self.database_insert is not None:
            self.database_insert.wait()  # wait for last insert to finish
        self.database_insert = self.db.query(query, threaded=True)

    def get_pmids_in_database(self, replace=True, test=False):
        """ Retrieves a list of all PMIDs collected in the database. Optionally run in test mode, which limits to 50 papers """
        limit = '' if not test else "LIMIT 50"

        self.log("Querying for PMIDs in database...")
        if test: self.log(f"TEST MODE ENABLED - {limit}")

        self.mark_time('query')
        if replace:
            query = f"SELECT DISTINCT pmid FROM documents {limit}"
        else:  # only PMIDs not already in the citation stats table
            query = f"""
            SELECT DISTINCT d.pmid FROM documents d
            LEFT JOIN {self.table_name} s ON d.pmid = s.pmid
            WHERE s.pmid is NULL
            {limit}
            """
        rows = self.db.query(query)
        if rows is None: rows = []
        self.add_time('query')
        self.log(f"Got {len(rows):,} documents from database ({self.get_time_total('query')})")
        self.clear_time('query')
        return [row['pmid'] for row in rows]

    def request(self, pmids):
        """ Request the given pmids from iCite """
        response = requests.get(f"{self.url}/pubs?pmids={','.join(pmids)}")
        if response.status_code != 200:
            self.debug(f"Got bad response from iCite API. Status Code: {response.status_code} - {response.reason}")
            data = {}
        else:
            data = response.json()  # JSON response data

        papers = data.get('data', [])  # list of papers and their data
        return papers

    def collect(self, pmids, batch_size=1000, insert=True, show_progress=True, threads=10):
        """
        Request data from the iCite API in batches and insert the result into the database.
        Threads requests to iCite, which seems to be able to handle ~10 requests of 1,000 papers at a time.
        """
        assert 1 <= batch_size <= 1000, "iCite API batch size must be from 1 to 1000"
        num = len(pmids)

        self.log(f"{num:,} papers with batch size {batch_size:,}")
        pmids = [str(pmid) for pmid in pmids]  # make sure they are all strings
        pmid_batches = self.batch_list(pmids, size=batch_size)

        self.debug(f"Threading requests to iCite using {threads} threads).")
        queue = ThreadQueue(threads)

        if show_progress:
            self.log("Progress | Total Time | Batch Time || Request | Insert")

        # submit all pmid batches to thread queue
        for batch in pmid_batches:
            queue.submit(self.request, [batch])

        total_batches = len(pmid_batches)
        total_papers = 0  # total papers whose stats were retrieved from icite
        for i, batch in enumerate(pmid_batches):
            self.mark_time('batch')

            self.mark_time("request")
            papers = queue.next()
            total_papers += len(papers)
            if papers is None:
                break  # queue empty
            self.add_time('request')

            rows = []
            for paper in papers:
                row = []
                for col in self.columns:
                    row.append(paper.get(col))
                rows.append(row)

            if insert:
                self.mark_time('insert')
                self.insert(rows)
                self.add_time('insert')

            self.add_time('batch')
            progress = self.progress(i, total_batches, every=1)
            if show_progress and progress:
                total_time = self.get_time_total('batch')
                batch_time = self.get_time_last('batch')
                request_time = self.get_time_last("request")
                insert_time = self.get_time_last("insert")
                self.log(f"{progress:8} | {total_time:10} | {batch_time:10} || {request_time:7} | {insert_time:6}")

        # wait for last insert to finish, if it hasn't already
        if self.database_insert is not None:
            self.database_insert.wait()

        self.log("Citation Stats Collection Complete.")
        self.log(f"Avg Batch Time: {self.get_time_avg('batch')}")
        self.log(f"Total papers received: {total_papers}")