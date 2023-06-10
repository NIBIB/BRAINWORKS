import json
import requests
import xmltodict
import datetime
from dateutil.parser import parse
import traceback
import math
import collections

import re
import os, sys
import time
from pathlib import Path

from utils.database.database import MySQLDatabase
from utils.generalPurpose.generalPurpose import *
from utils.affiliationParser import parse_affil, match_affil
from utils.base import Base, StoredDict, StoredList


class PubmedCollector(Base):
    """ Manages pulling and storing data from the PubMed Enrtrez API """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
        self.fetch_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
        #"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?id=36049039,36049040&db=pubmed&api_key=26000c321e5d45fa14e115f859303a77e808&retmode=xml&retmax=10000"

        # data storage directory
        self.data_directory = f"{self.config.data_directory}/collection"

        self.stored_files = StoredList("stored_files", self.data_directory, self.get_stored_files)
        self.stored_pmids = None

        # rate limiting
        self.requests_per_second = self.config.NCBI_rate_limit
        self.num_requests = 0
        self.max_request_tries = 10

        self.db = MySQLDatabase()

    def generateTables(self):
        """ Generates all necessary tables used to store the data """
        self.log('------------------------------------------------')
        self.log(' Creating PubMed Tables                         ')
        self.log('------------------------------------------------')

        query = """CREATE TABLE IF NOT EXISTS `application_types` (
                      `application_type`  int(11)      NOT NULL     COMMENT 'A numeric code for the application type.',
                      `description`       varchar(500) DEFAULT NULL COMMENT 'The meaning of the application code.',
                      PRIMARY KEY (`application_type`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
        self.db.query(query)
        self.log('.... `application_types` table created')

        query = """CREATE TABLE IF NOT EXISTS `citations` (
                  `pmid`          int(11)             DEFAULT NULL COMMENT 'The PubMed identification number of the paper being cited',
                  `citedby`       int(11)             DEFAULT NULL COMMENT 'The PubMed identification number of the paper that did the citing',
                  `citation_date` date                DEFAULT NULL COMMENT 'The date that the `pmid` was cited.',
                  `citation_num`  bigint(20) unsigned NOT NULL AUTO_INCREMENT,
                  PRIMARY KEY (`citation_num`),
                  UNIQUE KEY `citation_num`           (`citation_num`),
                  KEY `citations_pmid_index`          (`pmid`),
                  KEY `citations_pmiddate_index`      (`citation_date`,`pmid`),      
                  KEY `citations_citedby_index`       (`citedby`),
                  KEY `citations_citation_date_index` (`citation_date`)
                ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4
                """
        self.db.query(query)
        self.log('.... `citations` table created')

        query = """CREATE TABLE IF NOT EXISTS `documents` (
                  `element_id`    bigint(20) unsigned  NOT NULL AUTO_INCREMENT,
                  `pmid`          int(11)              DEFAULT NULL  COMMENT 'The PubMed identification number.',
                  `pub_date`      date                 DEFAULT NULL  COMMENT 'The full date on which the issue of the journal was published.',
                  `content_order` int(11)              NOT NULL      COMMENT 'The order of the element_id in a give pmid document. 1 preceeds 2 and so on.',
                  `content_type`  varchar(100)         DEFAULT NULL  COMMENT 'The content type of the element_id: figure, title, abstract, section, subsection, subsubsection, etc.',
                  `content` TEXT CHARACTER SET utf8mb4 DEFAULT NULL  COMMENT 'The text of the element_id container. If this were a `section` or instance, then this field would contain the name of the section.',
                  PRIMARY KEY (`element_id`),
                  FULLTEXT KEY `documents_content_index` (`content`),
                  KEY `documents_pmid_index`             (`pmid`),
                  KEY `documents_pub_date_index`         (`pub_date`),
                  KEY `documents_pmiddate_index`         (`pub_date`,`pmid`),
                  KEY `documents_type_index`             (`content_type`),
                  KEY `documents_order_index`            (`pmid`,`content_order`),
                  KEY `documents_element_id_index`       (`element_id`)
                ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4
                """
        self.db.query(query)
        self.log('.... `documents` table created')

        query = """CREATE TABLE IF NOT EXISTS `grants` (
                  `grant_num`  bigint(20)  unsigned NOT NULL AUTO_INCREMENT,
                  `grant_id`   varchar(30) DEFAULT NULL      COMMENT 'The grant ID',
                  `pmid`       int(11)     DEFAULT NULL      COMMENT 'The PubMed ID',
                  `pub_date`   date        DEFAULT NULL      COMMENT 'The full date on which the issue of the journal was published.',
                  PRIMARY KEY (`grant_num`),
                  UNIQUE KEY `grant_num`       (`grant_num`),
                  KEY `grants_grant_id_index`  (`grant_id`),
                  KEY `grants_pmid_index`      (`pmid`),
                  KEY `grants_pub_date_index`  (`pub_date`),
                  KEY `grants_pmiddate_index`  (`pub_date`,`pmid`)

                ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1
                """
        self.db.query(query)
        self.log('.... `grants` table created')

        query = """CREATE TABLE IF NOT EXISTS `id_map` (
                  `map_id`       bigint(20)   unsigned NOT NULL AUTO_INCREMENT,
                  `pmid`         int(11)      NOT NULL      COMMENT 'The PubMed ID',
                  `pub_date`     date         DEFAULT NULL  COMMENT 'The full date on which the issue of the journal was published.',
                  `pmc_id`       varchar(100) DEFAULT NULL  COMMENT 'The PubMed Central ID',
                  `nlm_id`       varchar(100) DEFAULT NULL  COMMENT 'Natonal Library of Medicine ID',
                  `doi`          varchar(100) DEFAULT NULL  COMMENT 'The Digital Object Identifier',
                  `issn_linking` varchar(100) DEFAULT NULL  COMMENT 'The ISSN Linking Number',
                  PRIMARY KEY (`map_id`),
                  UNIQUE KEY `map_id`       (`map_id`),
                  KEY `id_map_pmid_index`   (`pmid`),
                  KEY `id_pub_date_index`   (`pub_date`),
                  KEY `id_pmiddate_index`   (`pub_date`,`pmid`),
                  KEY `id_doi_index`        (`doi`)
                ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4
                """
        self.db.query(query)
        self.log('.... `id_map` table created')

        query = """CREATE TABLE IF NOT EXISTS `qualifiers` (
                  `qualifier_num` bigint(20) unsigned  NOT NULL AUTO_INCREMENT,
                  `pmid`          int(11)              NOT NULL     COMMENT 'The PubMed Indentification number.',
                  `pub_date`      date                 DEFAULT NULL COMMENT 'The full date on which the issue of the journal was published.',
                  `topic_id`      varchar(15)          NOT NULL     COMMENT 'A unique Medical Subject Heading Code that Identifies the topic this `qualifier_id` applies to.',
                  `qualifier_id`  varchar(15)          NOT NULL     COMMENT 'The Medical Subject Heading identification number for the qualifier that applies to the `topic_id`.',
                  `description`   varchar(100)         DEFAULT NULL COMMENT 'The text description of the `qualification_id`.',
                  `class`         varchar(15)          DEFAULT NULL COMMENT 'Indicates the importance of the qualification placed on the topic. Options:major, minor',
                  PRIMARY KEY (`qualifier_num`),
                  UNIQUE KEY `qualifier_num`            (`qualifier_num`),
                  KEY `qualifiers_pmid_topic_id_index`  (`pmid`,`topic_id`)
                ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4
                """
        self.db.query(query)
        self.log('.... `qualifiers` table created')

        query = """CREATE TABLE IF NOT EXISTS `topics` (
                  `topic_num`    bigint(20) unsigned NOT NULL AUTO_INCREMENT,
                  `pmid`         int(11)             NOT NULL     COMMENT 'The PubMed identification number.',
                  `pub_date`     date                DEFAULT NULL COMMENT 'The full date on which the issue of the journal was published.',
                  `source`       varchar(15)         DEFAULT NULL COMMENT 'The type of topic. Options: `MeSH`, `chemical`, `publication`',
                  `description`  varchar(100)        DEFAULT NULL COMMENT 'The text description of the `topic_id`.',
                  `topic_id`     varchar(15)         NOT NULL     COMMENT 'The unique Medical Subject Heading (MeSH) identification number for this topic.',
                  `class`        varchar(15)         DEFAULT NULL COMMENT 'The importance of the `topic_id` for the paper assocated with the `pmid`. Options:major, minor.',
                  PRIMARY KEY (`topic_num`),
                  UNIQUE KEY `topic_num`            (`topic_num`),
                  KEY `topics_pmid_class_index`     (`pmid`),
                  KEY `topics_pub_date_index`       (`pub_date`),
                  KEY `topics_pmiddate_index`       (`pub_date`,`pmid`),
                  KEY `topics_description_index`    (`description`),
                  KEY `topics_topic_id_index`       (`topic_id`)
                ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4
                """
        self.db.query(query)
        self.log('.... `topics` table created')

        # Affiliations Table
        query = """
        CREATE TABLE IF NOT EXISTS `affiliations` (
                  `affiliation_num`  bigint(20) unsigned NOT NULL AUTO_INCREMENT,
                  `pub_date`         date          DEFAULT NULL  COMMENT 'The full date on which the issue of the journal was published.',
                  `pmid`             int(11)       DEFAULT NULL  COMMENT 'The PubMed identification number.',
                  `first_name`       varchar(100)  DEFAULT NULL  COMMENT 'The first name of the author.',
                  `middle_name`      varchar(100)  DEFAULT NULL  COMMENT 'The midle name of the author.',
                  `last_name`        varchar(100)  DEFAULT NULL  COMMENT 'The last name of the author.',
                  `affiliation`      TEXT                        COMMENT 'The full affiliation string provided by PubMed.',
                  `department`       varchar(250)  DEFAULT NULL  COMMENT 'The inferred department of the author.',
                  `institution`      varchar(250)  DEFAULT NULL  COMMENT 'The inferred institution of the author.',
                  `location`         varchar(250)  DEFAULT NULL  COMMENT 'The inferred location of the author.',
                  `email`            varchar(250)  DEFAULT NULL  COMMENT 'The inferred email address of the author.',
                  `zipcode`          varchar(250)  DEFAULT NULL  COMMENT 'The inferred zipcode of the author.',
                  `country`          varchar(250)  DEFAULT NULL  COMMENT 'The inferred country of the author.',
                  `grid_id`          varchar(14)   DEFAULT NULL  COMMENT 'The inferred grid_id.',
                  `orcid_id`         varchar(50)   DEFAULT NULL  COMMENT 'The inferred ORCID id.',
                  PRIMARY KEY (`affiliation_num`),
                  UNIQUE KEY `affiliation_num`          (`affiliation_num`),
                  KEY `affiliations_pmid_index`         (`pmid`),
                  KEY `affiliations_pub_date_index`     (`pub_date`),
                  KEY `affiliations_pmiddate_index`     (`pub_date`,`pmid`),
                  KEY `affiliations_author_name_index`  (`last_name`,`first_name`),
                  FULLTEXT KEY `affiliation_index`      (`grid_id`)
                ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;
            """

        self.db.query(query)
        self.log('.... `affiliations` table created')

        # Publications
        query = """CREATE TABLE IF NOT EXISTS `publications` (
                  `pmid`               int(11) NOT NULL COMMENT 'A PubMed unique identifier. This field is a 1- to 8-digit accession number with no leading zeros.',
                  `pub_date`           date DEFAULT NULL COMMENT 'The full date on which the issue of the journal was published.',
                  `pub_title`          text COMMENT 'The title of the journal article. The title is always in English; those titles originally published in a non-English language and translated for the title field are enclosed in square brackets.',
                  `country`            varchar(100) DEFAULT NULL COMMENT 'The journals country of publication. Valid values are those country names found in the Z category of the Medical Subject Headings (MeSH)',
                  `issn`               varchar(100) DEFAULT NULL COMMENT 'The International Standard Serial Number, an eight-character value that uniquely identifies the journal.',
                  `journal_issue`      varchar(100) DEFAULT NULL COMMENT 'The issue, part, or supplement of the journal in which the article was published.',
                  `journal_title`      varchar(300) DEFAULT NULL COMMENT 'The full journal title, taken from NLMs cataloging data following NLM rules for how to compile a serial name.',
                  `journal_title_abbr` varchar(200) DEFAULT NULL COMMENT 'The standard abbreviation for the title of the journal in which the article appeared.',
                  `journal_volume`     int(11) DEFAULT NULL COMMENT ' The volume number of the journal in which the article was published.',
                  `lang`               varchar(100) DEFAULT NULL COMMENT 'The language(s) in which an article was published. See https://www.nlm.nih.gov/bsd/language_table.html. for options',
                  `page_number`        varchar(200) DEFAULT NULL COMMENT 'The inclusive pages for the article.  The pagination can be entirely non-digit data.  Redundant digits are omitted.  Document numbers for electronic articles are also found here.',
                  PRIMARY KEY (`pmid`),
                  KEY `publications_pmid_index`          (`pmid`),
                  KEY `publications_pub_date_index`      (`pub_date`),
                  KEY `publications_pmiddate_index`      (`pub_date`,`pmid`),
                  KEY `publications_journal_title_index` (`journal_title`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        self.db.query(query)
        self.log('.... `publications` table created')

    def rate_limit(self):
        """ Rate limit based on some number of calls per second """
        self.num_requests += 1  # increment number of requests
        if self.num_requests % self.requests_per_second == 0:  # if need to rate limit
            self.debug("RATE LIMIT")
            time.sleep(1)  # sleep for a second to accommodate rate limit

    # Working with downloaded papers
    def get_data_path(self, filename, date, sub, ext):
        """
        Returns the full file path to where the given file will be stored.
        Generates the directory structure when necessary.

        <filename> file name without extension
        <root> root path
        <date> datetime object with year, month, and day
        <sub>  optional subdirectory
        <ext>  file extension subdirectory

        Generated structure is as follows:
        -[root]
            -[year]
                -[month]
                    -[day]
                        -[sub]
                            -[ext]
            -0000_unknown_date
                -[sub]
                    -[ext]
        """

        root = self.data_directory

        if date is not None:
            # add nested date directories (0-padded)
            root = f"{root}/{date.year}/{date.month:02}/{date.day:02}"
        else:  # if date is none, place in unknown date directory
            root = f"{root}/0000_unknown_date"  # the 0000 are so this directory name is always numerically less than every other year.

        if sub is not None:  # if a subdirectory given, add that too
            root = f"{root}/{sub}"

        # Add the extension subdirectory
        if ext is not None:
            root = f"{root}/{ext}"

        os.makedirs(root, exist_ok=True)  # make directories if necessary
        return f"{root}/{filename}.{ext}"  # return full path to file

    def get_pub_date_from_path(self, file_path):
        """ Given a file path, return the pub date defined by self.get_data_path() """
        file_path = file_path.replace(f"{self.data_directory}/", '')  # remove root
        dirs = file_path.split('/')

        try:
            year, month, day = int(dirs[0]), int(dirs[1]), int(dirs[2])
            return datetime.date(year=year, month=month, day=day)
        except Exception as e:
            self.debug(f"Unable to identify a date from the given file path: {file_path}")
            return None

    def get_stored_files(self):
        """ Populates a dictionary to map PMIDs to the filenames of currently downloaded papers """
        self.log("Indexing all stored paper files... (could take a few minutes)")
        self.mark_time('t')
        files = [str(p) for p in Path(self.data_directory).rglob('fetch/**/*.json')]
        self.log(f"Found: {len(files):,} ({self.get_time_total('t')})")
        self.clear_time('t')

        self.log("Sorting by date ascending...")
        self.mark_time('t')
        files.sort()
        self.add_time('t')
        self.log(f"Sorted in {self.get_time_total('t')}")
        self.clear_time('t')
        return files

    def get_pmid_from_filename(self, filename):
        """ Convert from filename and PMID """
        filename = str(filename)
        a = filename.rfind('_') + 1
        b = filename.find('.')
        return filename[a:b]

    def get_database_pmids(self):
        """ Get set of all PMIDs already collected in database """
        self.log("Querying for all PMIDs in the database...")
        rows = self.db.query("""SELECT DISTINCT pmid FROM documents""")
        if not rows:
            self.log("No PMIDs found in database.")
            return []
        return set(str(r['pmid']) for r in rows)

    def get_document_field_stats(self, show_progress=True):
        """ Generates a json file detailing the stats of all JSON fields given by pubmed"""
        file_path = f"{self.data_directory}/field-statistics.stats"
        self.log('Generating field statistics from data:', file_path)
        total_files = len(self.stored_files)
        field_stats = collections.Counter([])

        # Initialize the field stats Counter.
        self.log(f'Ingesting {total_files:<,} papers... (this may take some time)')
        if show_progress:
            self.log(f"Progress |   Time   |  Read  |  Parse  | Total Papers")

        total_papers = len(self.stored_files)
        for i, filename in enumerate(self.stored_files):  # for each paper file
            self.mark_time('read')
            paper = self.get_paper(filename)
            if not paper: return
            self.add_time('read')

            self.mark_time('parse')
            # Flatten the paper
            x = flatten(paper, last_keys='', key_list=[], value_list=[])

            # Get the unique keys (so we do not double count author lists, for insntance.)
            keys = list(set([re.sub(r'_\d+_', '', a) for a in list(x.keys())]))

            # Add the field counts
            field_stats += collections.Counter(keys)
            self.add_time('parse')

            progress = self.progress(i, total_papers)
            if show_progress and progress:
                total = self.get_time_total('read', 0)
                read = self.get_time_sum('read', 1)
                parse = self.get_time_sum('parse', 1)
                self.log(f"{progress:<8} | {total:<8} | {read:<6} | {parse:<7} | {i+1:<,}")

        self.log("Converting to dict...")
        field_stats = dict(field_stats)

        self.log('Normalizing field counts...')
        for key, val in field_stats.items():
            field_stats[key] = round(100 * (val / total_files))

        self.log(f'Saving field statistics... ({file_path})')
        with open(file_path, "w") as f:
            json.dump(field_stats, f)

    def get_stored_pmids(self, force=False):
        """ Get set of all PMIDs stored on disk from the fetch utility """
        if self.stored_pmids is None or force:
            self.log("Getting all stored PMIDs...")
            self.stored_pmids = set()
            self.mark_time('t')
            for file in self.stored_files:
                self.stored_pmids.add(self.get_pmid_from_filename(file))
            self.log(f"Found: {len(self.stored_pmids):,} ({self.get_time_total('t')})")
            self.clear_time('t')
        return self.stored_pmids

    def get_papers(self, filenames, threaded=False):
        """ Get a list of full paper dicts stored on disk from the list of filenames """
        papers = []
        if threaded:
            results = self.parallelize(self.get_papers, [papers])
            for result in results:  # concatenate results
                papers += result
            return papers

        for filename in filenames:  # for each file
            data = self.get_paper(filename)
            if data: papers.append(data)
        return papers

    def get_paper(self, filename):
        """ Get a full paper dicts stored on disk from the given filename """
        try:
            with open(filename) as f:
                return json.load(f)
        except Exception as e:
            self.log(f"Error reading from paper file: {self.exc(e)}")
            return None

    def parse_paper(self, file):
        """
        Given a paper dict read from disk, porse it into database columns ready for insert structured like so:
        {
            table_1: ([col1, col2, col3, ...], [1, 2, 3, ...]),
            table_2: ([col1, col2, col3, ...], [1, 2, 3, ...]),
            ...
        }
        """
        self.mark_time("read")
        paper = self.get_paper(file)
        pub_date = self.get_pub_date_from_path(file)  # get the pub date this paper is stored in

        self.add_time("read")
        if not paper: return

        data = {}
        self.mark_time('parse')
        try:
            pmid = self.getPubPmid(paper)

            columns, parameters = self._extractAffiliations(paper, pmid, pub_date)
            data['affiliations'] = (columns, parameters)

            columns, parameters = self._extractDocument(paper, pmid, pub_date)
            data['documents'] = (columns, parameters)

            columns, parameters = self._extractIdMap(paper, pmid, pub_date)
            data['id_map'] = (columns, parameters)

            columns, parameters = self._extractGrants(paper, pmid, pub_date)
            data['grants'] = (columns, parameters)

            dcols, dparams, qcols, qparams = self._extractTopicsQualifiers(paper, pmid, pub_date)
            data['topics'] = (dcols, dparams)
            data['qualifiers'] = (qcols, qparams)

            columns, parameters = self._extractCitations(paper, pmid, pub_date)
            data['citations'] = (columns, parameters)

            columns, parameters = self._extractPublication(paper, pmid, pub_date)
            data['publications'] = (columns, parameters)
        except Exception as e:
            self.log(f"Error parsing paper data file: {file}")
            self.debug(f"{traceback.format_exc()}")
            return None

        self.add_time("parse")

        return data

    def parse_papers(self, papers, threaded=False):
        """
        Given a list of paper dict read from disk by self.get_papers(),
            create database columns ready for insert like so:
        {
            table_1: {columns: [col1, col2, col3, ...], values: [[1, 2, 3, ...], [4, 5, 6, ...]]},
            table_2: (columns: [col1, col2, col3, ...], values: [[1, 2, 3, ...], [4, 5, 6, ...]]},
            ...
        }
        """
        if threaded:
            self.debug("Submitting Papers to Thread: ", len(papers))
            results = self.parallelize(self.parse_paper, papers)
        else:
            results = []
            for paper in papers:
                results.append(self.parse_paper(paper))

        #print("done", len(results))
        total = len(results)
        results = [r for r in results if r is not None]
        #print('filtered', len(results))
        successes = len(results)
        fails = total - successes

        #self.log("DONE: ", successes, fails)
        data = {}
        for result in results:
            for table, (columns, values) in result.items():
                if data.get(table):
                    data[table]['values'] += values
                else:
                    data[table] = {'columns': columns, 'values': values}

        #self.log("DONE CONCATENATING", len(data), successes, fails)
        return data, successes, fails

    # Pulling from the Entrez API
    def search_pmids_by_date(self, date):
        """
        Search Entrez for PMIDs from the given date.
        <date> is a datetime object with year, month, and day.
        Returns the file path to the search result.
        Used to be: self.collect(query_params={'action':'search'})
        """

        # query parameters
        params = {
            "term": date.strftime("%Y/%m/%d") + "[pdat]",  # YYYY/MM/DD[pdat]
            "db": "pubmed",
            "api_key": self.config.NCBI_API_key,
            "retmode": 'xml',
            "retstart": 0,  # paper index
            "retmax": 100000,  # max queries to return in a single request (100,000 is the max allowed for searching)
        }

        pmids = []  # list of found pmids

        # Requests return a maximum number of papers (retmax) per batch,
        #   so it may need to be run multiple times if there are more
        #   papers than that.
        index = 0  # current paper index
        total = 1  # total papers to request (assume 1 at first)
        while index < total:
            params['retstart'] = index  # set query index to get
            response = self.make_entrez_request(self.search_url, params)
            filename = f"pubmed_{params['retstart']}_{date.strftime('%Y_%m_%d')}"  # name of the file to store this request

            # Save result as XML
            file_path = self.get_data_path(filename, date, "search", "xml")  # get full filepath
            with open(file_path, "w") as file:
                file.write(response.text)

            # Save result as JSON
            data_dict = xmltodict.parse(response.text)
            file_path = self.get_data_path(filename, date, "search", "json")  # get full filepath
            with open(file_path, "w") as file:
                json.dump(data_dict, file)

            search_result = data_dict.get('eSearchResult', {})
            if search_result.get('ERROR'):
                self.log(f"Entrez error: {search_result.get('ERROR')}")
                break

            total = int(search_result.get('Count') or 0)  # total number of papers
            # ret = int(search_result.get("RetMax") or 0)   # actual number of papers returned (may be less than total)
            id_list = search_result.get("IdList") or {}  # PMIDs. IdList key can exist and be null, or not exist
            id_list = id_list.get('Id') or []
            if type(id_list) != list:  # if just a single PMID
                id_list = [id_list]

            pmids += id_list  # add to list of PMIDs
            index += len(id_list)  # increment paper index

        return pmids

    def fetch(self, pmids, date=None, replace=False):
        """
        Downloads the full paper information from Entrez given a list of PMIDs.
        Requests in batches.
        <date> If provided, this date will be used as a backup for when the pub_date can't be found.
        <replace> is whether to replace the files already on disk if they already exist (slower).

        Returns a list of all filepaths written.
        """
        if not replace:  # if no replacement, filter out pmids already fetched
            collected = self.get_stored_pmids()  # get set of collected pmids
            pmids = list(set(pmids) - collected)

        params = {  # query parameters
            "id": '',  # set per batch
            "db": "pubmed",
            "api_key": self.config.NCBI_API_key,
            "retmode": 'xml',  # their json option appears to be broken :(
            "retmax": 10000  # number of papers to retrieve oer request (10,000 is the max allowed for fetching)
        }

        file_paths = []  # list of all file paths downloaded

        # no point in requesting more than 10,000 papers if that's the most we'll get back in a request, so batch the given pmids.
        pmid_batches = self.batch_list(pmids, 10000)  # list of lists
        for batch in pmid_batches:
            params['id'] = ','.join(batch)  # string of pmids for this batch
            response = self.make_entrez_request(self.fetch_url, params)
            if response is None:  # request failed
                continue
            data_dict = xmltodict.parse(response.content)  # convert XML to dict
            articles = self.get_article_list(data_dict)  # get list of articles from response
            self.debug(f"New PMIDs: {len(pmids)}, Fetched: {len(articles)}")

            for i, article in enumerate(articles):
                pmid = self.getPubPmid(article)  # read pmid from article
                pub_date = self.getPubDate(article, date)  # look for pub date in paper data, or use the date used to search it

                # Save as JSON
                file_path = self.get_data_path(f"pubmed_{pmid}", pub_date, "fetch", "json")  # get full filepath

                with open(file_path, "w") as f:
                    json.dump(article, f)
                file_paths.append(file_path)

        self.stored_files.extend(file_paths)  # add to stored filepaths
        return file_paths

    def make_entrez_request(self, url, params):
        """
        Makes a request to the Entrez API
        Returns the raw result.
        """
        self.debug('Entrez Query:\n', {p:str(v)[:100]+'...' if len(str(v))>100 else '' for p,v in params.items()}, '\n')

        tries = 1
        while tries < self.max_request_tries:
            self.rate_limit()  # wait if rate limit hit

            error = False
            response = requests.post(url, data=params)

            if not response.ok:
                self.log(f"Entrez request failed with staus code: {response.status_code} - {response.reason}")
                error = True
            elif not response.content:
                self.log(f"Got no content from entrez request.")
                error = True

            if error:  # error - try again
                tries += 1
                continue
            elif tries > 1:  # no error, but it did fail before
                self.log(f"Success after retried {tries} times.")
                return response
            else:  # no errors
                return response
        else:  # if tried too many times
            self.log(f"Entrez request failed {self.max_request_tries} times in a row. Aborting.")
            self.log("URL: ", url)
            self.log("Params: ", params)
            return None

    def bulk_collect(self, start_date, end_date=None, replace=False, reverse=True, show_progress=True):
        """
        Search and Fetch papers in the given date range.
        Packages requests to the Entrez Eutil to improve collection speed.
        <start>, <end> : datetime objects
        <replace> whether to replace paper files already on disk (slower if already have a bunch)
        """
        if not end_date:  # none given, default to current date.
            end_date = datetime.datetime.now().date()
        assert start_date <= end_date, f"Start date must be less than end date. Got: {start_date}, {end_date}"

        if not replace:
            self.get_stored_pmids()  # preemptively get PMIDs already collected

        self.log('------------------------------')
        self.log('Starting Bulk Paper Collection')
        self.log("Replacement is ENABLED." if replace else "Replacement is DISABLED.")
        self.log(f"Searching time range from {self.date_string(start_date)} to {self.date_string(end_date)}{' (in reverse)' if reverse else ''}.")

        total_searched = 0
        total_fetched = 0

        if show_progress:
            self.log(f"   Date   |  Searched  |  Fetched  |   Time   | Avg Time | Total Time | Total Fetched")

        if reverse:
            current_date = end_date
        else:
            current_date = start_date

        while (reverse and current_date >= start_date) or (not reverse and current_date <= end_date):
            date_string = self.date_string(current_date)
            self.mark_time('day')  # start timing

            searched = 0  # number of pmids returned from search
            fetched = 0  # number of papers returned from fetch
            try:
                pmids = self.search_pmids_by_date(current_date)  # search pmids on this date
                searched = len(pmids)
                pmids = self.fetch(pmids, date=current_date, replace=replace)  # fetch paper data for these pmids
                fetched = len(pmids)
            except Exception as e:
                self.log(f"Collection for {date_string} failed. {e.__class__.__name__}: {e}")
                self.debug(traceback.format_exc())
            self.add_time('day')  # add time

            total_searched += searched
            total_fetched += fetched
            if show_progress:
                total = self.get_time_total('day', 0)
                avg = self.get_time_avg('day', 1)
                last = self.get_time_last('day', 1)
                self.log(f"{date_string:<10} | {searched:<10,} | {fetched:<9,} | {last:<8} | {avg:<8} | {total:<10} | {total_fetched:,}")

            # Increment the date
            if reverse:
                current_date = current_date - datetime.timedelta(days=1)
            else:
                current_date = current_date + datetime.timedelta(days=1)

        self.log(f"Bulk Collection Complete. Searched {total_searched:,} and Fetched {total_fetched:,} in {self.get_time_total('day')}")
        self.display_memory()  # display memory usage in debug mode

    def insert_papers(self, replace=False, reverse=True, show_progress=True, batch_size=10000, limit=None):
        """
        Process basic information from all papers on disk to store in database
        <limit> is a temporary way to limit the number of papers inserted for testing purposes.
        """
        self.log('------------------------------')
        self.log('Starting Paper Parsing')
        papers = self.stored_files  # list of all stored filenames
        self.log(f"Found {len(papers):,} stored files.")

        if limit:
            self.log(f"Limiting Papers Processed: {limit}")
            papers = papers[:limit]

        if not replace:  # if no replacement, filter out papers already inserted
            collected = self.get_database_pmids()
            new_papers = []
            self.log(f"Found {len(collected):,} papers already in the database.")
            self.log("Filtering for papers not yet inserted...", end='')
            self.mark_time('f')
            for filename in papers:
                pmid = self.get_pmid_from_filename(filename)
                if pmid in collected: continue
                new_papers.append(filename)
            self.log(f" Done ({self.get_time_total('f')})")
            self.clear_time('f')
            papers = new_papers

        papers.sort(reverse=reverse)  # sort file paths (which sorts by date)

        total_papers = len(papers)
        total_fails = 0
        total_successes = 0

        if show_progress:
            self.log()
            self.log(f"New papers to process: {total_papers:,} (with batch size {batch_size:,})")
            self.log(f"Batch | Progress |   Time   | Batch Time | Read Time | Parse Time | Insert Time | Batch Time/Paper | Memory")
            self.log(f"-----------------------------------------------------------------------------------------------------------")

        batches = self.batch_list(papers, batch_size)
        total_batches = len(batches)
        threads = []  # list of async database insert results to wait on

        for i, batch in enumerate(batches):  # for each batch of paper data
            self.mark_time('batch')
            self.mark_time('parse')
            data, successes, fails = self.parse_papers(batch, threaded=False)
            self.add_time('parse')
            total_successes += successes
            total_fails += fails

            # Insert this batch
            self.mark_time('insert')
            for result in threads:  # wait for previous inserts to finish if they haven't already
                if result is None: continue
                result.wait()
            threads = []
            for table, params in data.items():  # insert
                columns = params['columns']
                values = params['values']
                result = self.db.insert_row(table=table, columns=columns, parameters=values, threaded=True)
                if result is not None:
                    threads.append(result)  # add to list of results to wait() next loop
            self.add_time('insert')
            self.add_time('batch')

            if show_progress:
                progress = self.progress(i, total_batches, every=1)  # show progress% every batch
                total_time = self.get_time_total('batch', 0)  # time since start
                batch_time = self.get_time_last('batch', 2)  # last batch time
                avg_paper = self.get_time_avg('batch', 5, divisor=batch_size)  # total time/paper
                read_time = self.get_time_sum('read', 2)  # batch summed read time
                parse_time = self.get_time_sum('parse', 2)  # batch summed parse time
                insert_time = self.get_time_last('insert', 1)  # last batch insert time
                self.clear_time('read')
                self.clear_time('parse')
                self.log(f"{i+1:5} | {progress:8} | {total_time:8} | {batch_time:10} | {read_time:9} | {parse_time:10} | {insert_time:11} | {avg_paper:16} | {self.memory()}")

        self.log(f"Processing Complete. Succeeded: {total_successes:,} | Failed: {total_fails:,}")
        self.log(f"Total Time: {self.get_time_total('batch')}")
        self.log(f"Avg Batch Time: {self.get_time_avg('batch', 2)}")
        self.log(f"Avg Time/Paper: {self.get_time_avg('batch', 2, divisor=batch_size)}")

    ###############

    def downloadCitedPapersByPubmedId(self, write_location = 'data/PubMed', replace_existing = False, batch_size = 100):
        """ Collects all papers that were cited by papers already in the `publications` table. """
        print('---------------------------------------------')
        print('Looking for pmids in the `citations` without a matching entry in `publications`...')
        print('---------------------------------------------')

        # Take pmids from the `citations` that are not in publications table
        pmids_in_database = self.db.query("""SELECT distinct citations.pmid  
                                          FROM citations
                                          LEFT JOIN publications on publications.pmid = citations.pmid
                                         WHERE publications.pmid is NULL
                                      """)

        pmids_collected = self.get_database_pmids()

        # Remove those pmids that have already been downloaded
        pmids_in_database = [str(pmid['pmid']) for pmid in pmids_in_database]
        pmids             = list(set(pmids_in_database) -  set(pmids_collected))

        self.log("... Found", len(pmids), "entries without matching publication.")
        self.fetch_pmids(pmids)
        self.log(len(pmids), 'new files downloaded')

    def downloadExporterPapersByPubmedId(self, write_location = 'data/PubMed', replace_existing = False, batch_size = 100):
        """ Downloads all papers from the `link_tables`, i.e. those from EXPORTER """
        print('------------------------------------------------------------------------------------')
        print('Looking for pmids in the `link_tables` without a matching entry in `publications`...')
        print('------------------------------------------------------------------------------------')

        #-------------------------------------------------------------------
        # Take pmids from the `link_tables` that are not in publications table
        #--------------------------------------------------------------------
        pmids_in_database = self.db.query("""SELECT distinct link_tables.pmid  
                                         FROM link_tables
                                         LEFT JOIN publications on publications.pmid = link_tables.pmid
                                         WHERE publications.pmid is NULL
                                      """)
        # Remove those pmids that have already been downloaded
        pmids_in_database = [str(pmid['pmid']) for pmid in pmids_in_database]
        pmids_downloaded  = self.get_database_pmids()
        pmids             = list(set(pmids_in_database) - set(pmids_downloaded))

        print("... Found", len(pmids), "entries without matching publication.")
        print("... Collecting new papers...")

        filenames = self.fetch_pmids(pmids)
        self.log(f"Fetched {len(filenames)} new papers")

    ######################################################################
    # Checks if a dict satisfies a set of key, and value criteria
    ######################################################################
    def extractFromPubmedData(self, flat_data, key_has = [], value_has = [], fetch_part = None ):

        try:

            data_elements = flat_data.keys()
            # See if this key matches the criteria

            results = []

            for element in data_elements:

                # Key Critera
                key_critera = True
                for key in key_has:
                    if key not in element.lower():
                        key_critera = False

                # See if the value matches this critera
                value_criteria = True
                for value in value_has:
                    if value not in flat_data[element].lower():
                        value_criteria = False

                if key_critera and value_criteria:
                    if fetch_part is not None:
                        results.append(flat_data['.'.join(element.split('.')[:-1] + [fetch_part])])
                    else:
                        results.append(flat_data[element])

            return list(set(results))
        except Exception as e:
            return []

    def get_json_key(self, data, key_paths, default=None, search=False):
        """
        Gets information from a given dictionary in JSON-like format.
        <key_paths> is a list of lists of strings, which are dict keys to search for the item in order of prescedence.
        <search> is whether to search the whole dict if all paths fail.
        """
        for i, path in enumerate(key_paths):
            result = data
            try:
                for key in path:  # follow this path
                    r = result.get(key)
                    if r is None: break  # if not found, try next path
                    result = r  # otherwise move deeper
                else:  # didn't break - full path traversed and result found
                    return result, i

            except Exception as e:
                if i+1 == len(key_paths):  # this was the last key path.
                    self.debug(f"Exception getting key from dict. Path: {path}, Key: {key}, Failed at: {result}")
                continue  # try the next key path

        return default, None

    def get_article_list(self, data):
        """ Get a list of articles from the given dict """
        p1 = ['PubmedArticleSet', 'PubmedArticle']
        #p2 = ['PubmedArticleSet', 'PubmedBookArticle']  # TODO implement parseing book articles
        articles, i = self.get_json_key(data, [p1])
        if not articles:
            return []
        if not type(articles) == list:  # if not a list of articles, it's just one article
            articles = [articles]

        # now add back on the ArticleSet and whatnot for each because everything else relies on it
        # TODO get rid of that from all stored articles
        for j, article in enumerate(articles):
            articles[j] = {'PubmedArticleSet': {'PubmedArticle': article}}
        return articles

    def getDoi(self, elocation):
        """ Get the DOI from pubmed data"""
        elocation =  [elocation] if isinstance(elocation, dict) else elocation
        _doi = [None]
        for location in elocation:
            if location.get('@EIdType') == 'doi' and location.get('@ValidYN') == 'Y':
                _doi = [location.get('#text')]
        return _doi[0]

    def getPubDate(self, paper, backup=None):
        """ Get the publication date of an article in DICT form loaded from JSON from Entrez """
        p1 = ['PubmedArticleSet', 'PubmedArticle', 'MedlineCitation', 'ArticleDate']
        p2 = ['PubmedArticleSet', 'PubmedArticle', 'MedlineCitation', 'Journal', 'JournalIssue', 'PubDate']
        #p3 = ['PubmedArticleSet', 'PubmedBookArticle', 'BookDocument', 'Book', 'PubDate']
        pubdate, i = self.get_json_key(paper, [p1, p2])

        try:
            year = pubdate.get('Year')
            month = 'Jan' if pubdate.get('Month') is None else pubdate.get('Month')
            day = '1' if pubdate.get('Day') is None else pubdate.get('Day')
            date = parse(f"{year}-{month}-{day}", ) if year is not None else None
            date = date.date()
        except Exception as e:
            date = backup
        return date

    def getPubPmid(self, paper):
        """ Get pmid from paper dict """
        # strip away the base keys that all papers have
        p1 = ['PubmedArticleSet', 'PubmedArticle', 'MedlineCitation', "PMID", "#text"]
        #p2 = ['PubmedArticleSet', 'PubmedBookArticle', 'BookDocument', "PMID", "#text"]
        pmid, i = self.get_json_key(paper, [p1])
        return pmid

    def getPubTitle(self, paper):
        """ Get an article's title from the given JSON pubmed data """
        # strip away the base keys that all papers have
        p1 = ['PubmedArticleSet', 'PubmedArticle', 'MedlineCitation', 'Article', 'ArticleTitle', "#text"]
        p2 = ['PubmedArticleSet', 'PubmedArticle', 'MedlineCitation', 'Article', 'ArticleTitle']
        #p2 = ['PubmedArticleSet', 'PubmedBookArticle', 'BookDocument', 'Book', 'CollectionTitle', "#text"]
        title, i = self.get_json_key(paper, [p1, p2])
        return title

    def _extractAffiliations(self, paper_json, paper_id, pub_date):
        """ Extracts and parses author affiliations """
        columns, parameters = ['pub_date','pmid','last_name','first_name','middle_name','affiliation',
                               'department','institution','location','email',
                               'country','grid_id','orcid_id'], []

        medline_citation  = paper_json.get('PubmedArticleSet', {}).get('PubmedArticle', {}).get('MedlineCitation', {})
        author_list       = medline_citation.get('Article',{}).get('AuthorList', {}).get('Author',{})
        author_list       = [author_list] if not isinstance(author_list, list) else author_list
        _author_list      = []
        _affiliation_list = []

        for author in author_list:
            a = author.get('AffiliationInfo', {})

            affiliations =  [a] if not isinstance(a, list) else a
            for i, affiliation in enumerate(affiliations):

                # Skip this if there is no author information.
                if author.get('LastName') is None and author.get('ForeName') is None:
                    continue

                _pmid        = paper_id
                _last_name   = str(author.get('LastName'))
                forename     = str(author.get('ForeName')).split(' ')
                _first_name  = forename[0]
                _middle_name = ' '.join(forename[1:]) if len(forename) > 1 else None
                _affiliation = affiliation.get('Affiliation')


                if _affiliation is not None:
                    _email       = ';'.join(re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', _affiliation))

                    match        = re.search(r'\d{4}\-\d{4}\-\d{4}\-\d{3}(?:\d|X)', _affiliation)
                    _orcid_id    = match.group(0) if match is not None else None


                    _parsed_affil   = parse_affil(_affiliation)
                    #_grid_id       = match_affil(_affiliation)[0]['grid_id']
                    _grid_id        = None

                    if _parsed_affil['institution'] is not None and _parsed_affil['department'] is not None:
                        _parsed_affil['institution'] = _parsed_affil['institution'].replace(_parsed_affil['department'],'')

                    _country       = _parsed_affil['country']     if _parsed_affil['country']     != '' else None
                    _department    = _parsed_affil['department']  if _parsed_affil['department']  != '' else None
                    _institution   = _parsed_affil['institution'] if _parsed_affil['institution'] != '' else None
                    _location      = _parsed_affil['location']    if _parsed_affil['location']    != '' else None
                else:
                    _email         = None
                    _orcid_id      = None
                    _country       = None
                    _department    = None
                    _institution   = None
                    _location      = None
                    _grid_id       = None


                parameters.append([pub_date, _pmid, _last_name, _first_name, _middle_name, _affiliation,
                                   _department, _institution, _location, _email,
                                   _country, _grid_id, _orcid_id])

        # convert to list of lists
        if not any(isinstance(x, list) for x in parameters):
            parameters = [parameters]

        parameters = [x for x in parameters if x != []]
        return columns, parameters

    def _extractDocument(self, paper_json, paper_id, pub_date):
        """ Extracts the Abstract and Title from the pubmed document """
        columns    = ['pmid','pub_date','content_order','content_type','content']

        # Format the data
        x  = flatten(paper_json, last_keys='',key_list=[], value_list=[])

        # Abstract
        abstract_candidates = [x[a] for a in x.keys() if ('abstracttext' in a.lower()) and (len(x[a].split()) > 1) and ('@Label' not in a.lower()) and ('@NlmCategory' not in a.lower())]
        abstract           = ' '.join(abstract_candidates)
        if abstract.isspace() or abstract == '':
            abstract = None

        # Title
        title = self.getPubTitle(paper_json)

        parameters = [
            [int(paper_id), pub_date, 1, 'title', title],
            [int(paper_id), pub_date, 2, 'abstract', abstract]
        ]
        return columns, parameters

    def _extractIdMap(self, paper_json, paper_id, pub_date):
        """ Extracts the various IDs from the pubmed data: PMC, NLP, ISSN, ETC. """
        columns    = ['pmid','pub_date','pmc_id','nlm_id','doi','issn_linking']

        medline_citation     = paper_json.get('PubmedArticleSet', {}).get('PubmedArticle', {}).get('MedlineCitation', {})

        # Format the data
        x = flatten(paper_json, last_keys='',key_list=[], value_list=[])

        # eLocation
        elocation = medline_citation.get('Article',{}).get('ELocationID',{})
        _location = self.getDoi(elocation)

        # Get the Pubmed Central ID
        pmc_candidates  = self.extractFromPubmedData( flat_data = x, key_has=['@IdType'.lower()], value_has=['pmc'],fetch_part='#text')
        _pmc            = [x for x in pmc_candidates if x[0:3] == "PMC"]
        _pmc = _pmc[0] if _pmc != [] else None

        # NLM and ISSN Linking IDS
        _nlmid       = self.extractFromPubmedData( flat_data = x, key_has=['nlmuniqueid'], value_has=[])
        _nlmid = _nlmid[0] if _nlmid != [] else None

        _issnLinking = self.extractFromPubmedData( flat_data = x, key_has=['issnlinking'], value_has=[])
        _issnLinking = _issnLinking[0] if _issnLinking != [] else None

        # Insert results into the database

        parameters = [ paper_id, pub_date, _pmc, _nlmid, _location, _issnLinking]

        # convert to list of lists
        if not any(isinstance(x, list) for x in parameters):
            parameters = [parameters]

        parameters = [x for x in parameters if x != []]
        return columns, parameters

    def _extractGrants(self, paper_json, paper_id, pub_date):
        """ Extracts the grants information from the pubmed data """
        columns     = ['grant_id','pmid','pub_date']

        # Format the data
        x = flatten(paper_json, last_keys='',key_list=[], value_list=[])
        parameters       = []

        _grantIDs   = self.extractFromPubmedData( flat_data = x, key_has=['grantid'], value_has=[])

        parameters  = []
        for grant in _grantIDs:
            parameters.append([grant, paper_id, pub_date])

        # convert to list of lists
        if not any(isinstance(x, list) for x in parameters):
            parameters = [parameters]

        parameters = [x for x in parameters if x != []]
        return columns, parameters

    def _extractTopicsQualifiers(self, paper_json, paper_id, pub_date):

        qcols  = ['pmid','pub_date','topic_id', 'qualifier_id', 'description', 'class']
        dcols  = ['pmid','pub_date','source', 'description', 'topic_id', 'class']

        # Medical Subject Headings -----------------------------------------------------------------
        medline_citation     = paper_json.get('PubmedArticleSet', {}).get('PubmedArticle', {}).get('MedlineCitation', {})
        MeshHeadingList      = medline_citation.get('MeshHeadingList',{}).get('MeshHeading',{})
        MeshHeadingList      =  [MeshHeadingList] if isinstance(MeshHeadingList, dict) else MeshHeadingList
        _mesh = []
        dparams, qparams = [],[]

        for mesh in MeshHeadingList:
            # Get the descriptor information
            descriptor         = mesh.get('DescriptorName',{})
            _topic_id          = descriptor.get('@UI')
            _topic_class       = 'major' if descriptor.get('@MajorTopicYN',{}) == 'Y' else 'minor'
            _topic_description = descriptor.get('#text')

            if _topic_id is None:
                continue

            # Store the descriptor information
            dparams.append([paper_id, pub_date, 'MeSH', _topic_description, _topic_id, _topic_class])

            # Get the qualifier information
            qualifiers = mesh.get('QualifierName')
            if qualifiers is None:
                continue

            qualifiers =  [qualifiers] if not isinstance(qualifiers, list) else qualifiers
            for qualifier in qualifiers:
                # For each qualifier
                _qualifier_id          = qualifier.get('@UI')
                _qualifier_class        = 'major' if qualifier.get('@MajorTopicYN') == 'Y' else 'minor'
                _qualifier_description = qualifier.get('#text')

                #Store the qualifier information
                qparams.append([paper_id, pub_date, _topic_id, _qualifier_id, _qualifier_description , _qualifier_class])


        # Chemicals------------------------------------------------------------------------
        ChemicalList = medline_citation.get('ChemicalList',{}).get('Chemical',{})
        ChemicalList = [ChemicalList] if isinstance(ChemicalList, dict) else ChemicalList
        parameters = []
        for chem in ChemicalList:
            if chem == {}:
                continue
            _topic_id          = chem.get('NameOfSubstance',{}).get('@UI')
            _topic_class       = None
            _topic_description = chem.get('NameOfSubstance',{}).get('#text')
            dparams.append([paper_id, pub_date, 'MeSH', _topic_description, _topic_id, _topic_class])

        # Publication Info------------------------------------------------------------------------
        try:
            publicationtypelist  = medline_citation.get('Article',{}).get('PublicationTypeList',{}).get('PublicationType',{})
        except Exception as e:
            publicationtypelist  = {}

        publicationtypelist =  [publicationtypelist] if isinstance(publicationtypelist, dict) else publicationtypelist
        parameters = []
        for pub in publicationtypelist:
            if pub == {}:
                continue
            _topic_id          = pub.get('@UI')
            _topic_class       = None
            _topic_description = pub.get('#text')
            dparams.append([paper_id, pub_date, 'MeSH', _topic_description, _topic_id, _topic_class])

        # convert to list of lists
        if not any(isinstance(x, list) for x in dparams):
            dparams = [dparams]
        dparams = [x for x in dparams if x != []]

        # convert to list of lists
        if not any(isinstance(x, list) for x in qparams):
            qparams = [qparams]
        qparams = [x for x in qparams if x != []]

        return dcols, dparams, qcols, qparams

    def _extractCitations(self, paper_json, paper_id, pub_date):
        columns   = ['pmid','citedby', 'citation_date']

        medline_citation     = paper_json.get('PubmedArticleSet', {}).get('PubmedArticle', {}).get('MedlineCitation', {})
        pubmed_data          = paper_json.get('PubmedArticleSet', {}).get('PubmedArticle', {}).get('PubmedData',{})


        try:
            Reference = pubmed_data.get('ReferenceList',{}).get('Reference')
        except Exception as e:
            Reference = []

        Reference = [] if Reference is None else Reference

        parameters = []
        for ref in Reference:

            # If this is a string - pass.
            if isinstance(ref, str):
                continue

            articlelist = ref.get('ArticleIdList',{}).get('ArticleId')
            if not isinstance(articlelist, list):
                articlelist = [articlelist]

            for ar in articlelist:
                if ar is None:
                    continue
                IdType = ar.get('@IdType')
                if IdType == 'pubmed':
                    cited_by = ar.get('#text')
                    parameters.append([int(cited_by), int(paper_id), pub_date])

        # convert to list of lists
        if not any(isinstance(x, list) for x in parameters):
            parameters = [parameters]
        parameters = [x for x in parameters if x != []]
        return columns, parameters

    def _extractPublication(self, paper_json, paper_id, pub_date):
        columns = [ 'country', 'issn', 'journal_issue', 'journal_title', 'journal_title_abbr', 'journal_volume', 'lang', 'page_number', 'pmid', 'pub_date', 'pub_title']

        medline_citation    = paper_json.get('PubmedArticleSet', {}).get('PubmedArticle', {}).get('MedlineCitation', {})
        pubmed_data         = paper_json.get('PubmedArticleSet', {}).get('PubmedArticle', {}).get('PubmedData',{})
        journal             = medline_citation.get('Article',{}).get('Journal',{})

        _title              = self.getPubTitle(paper_json)
        _country            = medline_citation.get('MedlineJournalInfo',{}).get('Country')
        _issn               = journal.get('ISSN',{}).get('#text')
        _journal_volume     = journal.get('JournalIssue',{}).get('Volume')
        _journal_issue      = journal.get('JournalIssue',{}).get('Issue')
        _journal_title      = journal.get('Title')
        _journal_title_abbr = journal.get('ISOAbbreviation')
        _page_number        = medline_citation.get('Article',{}).get('Pagination',{}).get('MedlinePgn')

        _language           = medline_citation.get('Article',{}).get('Language')
        if isinstance(_language, list):
            if len(_language) > 0:
                _language = _language[0]


        parameters = [_country, _issn, _journal_issue, _journal_title, _journal_title_abbr,_journal_volume, _language, _page_number, paper_id, pub_date, _title]

        # convert to list of lists
        if not any(isinstance(x, list) for x in parameters):
            parameters = [parameters]
        parameters = [x for x in parameters if x != []]

        return columns, parameters
