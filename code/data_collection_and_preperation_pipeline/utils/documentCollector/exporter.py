from utils.generalPurpose.generalPurpose import *
from utils.database.database import MySQLDatabase
from dateutil.parser import parse
import json
import requests
import datetime
import time
import glob
import re
import wget
from zipfile import ZipFile
from csv import reader
import math
import numpy as np
import shutil
import os, ssl


from utils.base import Base


#if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)):
    #ssl._create_default_https_context = ssl._create_unverified_context


exporter_primary_keys =  { 'abstracts'    : ['application_id', 'version'],
                           'publications' : ['pmid'],
                           'projects'     : ['application_id', 'version'],
                           'patents'      : ['patent_id', 'project_id'],
                           'afilliations' : ['pmid','author_name']}


class Exporter(Base):
    """ Handles collection from the ExPORTER API"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url  = "https://reporter.nih.gov/services/exporter"
        self.temp = "_temp_exporter_file"  # filename to temporarily save downloaded files to
        self.save_directory = f"{self.config.data_directory}/ExPORTER"
        self.document_list  = []

        # Connect to the Database
        self.db = MySQLDatabase()

        if not os.path.exists(self.save_directory):
            os.makedirs(self.save_directory)

    def run(self, replace=False):
        """ Run full ExPORTER collection pipeline """
        tables = ['projects','abstracts','patents','link_tables']
        self.generate_tables(replace)  # generate tables if they don't exist
        self.request(replace, tables)  # request data from exporter
        self.unpack_data(replace, tables)  # unzip and parse data
        self.import_data(replace, tables)  # insert into database

    def generate_tables(self, replace=False):
        """
        # This Function generates MySQL Tables using the ExPORTER Data Characteristics or static defintions.
        # -----------------------------------------------------------------------------------------------
        # INPUTS
        # replace_existing    <Bool>   - When True, all previously downloaded files are replaced.
        # -----------------------------------------------------------------------------------------------
        # OUTPUTS
        # Execute a query "SHOW TABLES" in MySQL to see the results of this function
        """
        create_table_queries = {}

        # Abstracts Table
        create_table_queries['abstracts'] = """CREATE TABLE IF NOT EXISTS `abstracts` (
                                  `year`            int(11) DEFAULT NULL COMMENT 'The year that the grant abstract was published',
                                  `application_id`  int(11) NOT NULL COMMENT 'A unique identifier of the project record',
                                  `abstract_text`   text COMMENT 'An abstract of the research being performed in the project. The abstract is supplied to NIH by the grantee.',
                                  `source`          varchar(200) DEFAULT NULL COMMENT 'Indicates where this information was collected from.',
                                  `version`         int(11) NOT NULL DEFAULT '0' COMMENT 'Says the version of the data from the `source` field',
                                  PRIMARY KEY (`application_id`,`version`),
                                  FULLTEXT KEY `abstract_text_index` (`abstract_text`)
                                ) ENGINE=InnoDB DEFAULT CHARSET=latin1
                            """

        # Link Tables
        create_table_queries['link_tables'] = """CREATE TABLE IF NOT EXISTS `link_tables` (
                                  `id`             bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
                                  `year`           int(11) DEFAULT NULL COMMENT 'The year that the link was established',
                                  `pmid`           int(11) DEFAULT NULL COMMENT 'The PubMed identification number',
                                  `project_number` varchar(100) DEFAULT NULL COMMENT 'An identifier of the research project either cited in the publication acknowledgements section or reported to have provided support in the NIH Public Access manuscript submission system.',
                                  `source`         varchar(200) DEFAULT NULL COMMENT 'Indicates the source of this information.',
                                  `version`        int(11) DEFAULT '0' COMMENT 'Indicates the version of this information collected from the `source`.',
                                  PRIMARY KEY (`id`),
                                  KEY `link_tables_pmid_index` (`pmid`),
                                  KEY `link_tables_project_number_index` (`project_number`),
                                  KEY `link_tables_year_index` (`year`)
                                ) ENGINE=InnoDB DEFAULT CHARSET=latin1
                            """

        # Patents Table
        create_table_queries['patents'] = """CREATE TABLE IF NOT EXISTS `patents` (
                              `year`            int(11) DEFAULT NULL COMMENT 'Indicates the year this patent was published.',
                              `patent_id`       int(11) NOT NULL COMMENT 'A unique alpha-numeric code which identifies a federal patent.',
                              `patent_title`    varchar(300) DEFAULT NULL COMMENT 'Title of the patent as it appears in the US Patent and Trademark Office database of issued patents.',
                              `project_id`      varchar(100) NOT NULL COMMENT 'An identifier of the research project acknowledged as supporting development of the patent.',
                              `patent_org_name` varchar(100) DEFAULT NULL COMMENT 'The name of the educational institution, research organization, business, or government agency receiving the patent.',
                              `source`          varchar(200) DEFAULT NULL COMMENT 'Indicates the source of this information.',
                              `version`         int(11) DEFAULT '0' COMMENT 'Indicates the version of this information collected from the `source`.',
                              PRIMARY KEY (`patent_id`,`project_id`),
                              FULLTEXT KEY `patents_patent_title_index` (`patent_title`)
                            ) ENGINE=InnoDB DEFAULT CHARSET=latin1
                            """

        # Projects Table
        create_table_queries['projects'] = """CREATE TABLE IF NOT EXISTS `projects` (
                              `year` int(11) DEFAULT NULL COMMENT 'The year that the project was funded.',
                              `application_id` int(11) NOT NULL COMMENT 'A unique identifier of the project record in the ExPORTER database.',
                              `activity` varchar(100) DEFAULT NULL COMMENT ' A 3-character code identifying the grant, contract, or intramural activity through which a project is supported.  Within each funding mechanism, NIH uses 3-character activity codes (e.g., F32, K08, P01, R01, T32, etc.) to differentiate the wide variety of research-related programs NIH supports.',
                              `administering_ic` varchar(100) DEFAULT NULL COMMENT 'Administering Institute or Center - A two-character code to designate the agency, NIH Institute, or Center administering the grant.',
                              `application_type` int(11) DEFAULT NULL COMMENT 'A one-digit code to identify the type of application funded. See `application_types` table for descriptions of the codes.',
                              `arra_funded` varchar(100) DEFAULT NULL COMMENT 'Y indicates a project supported by funds appropriated through the American Recovery and Reinvestment Act of 2009.',
                              `award_notice_date` varchar(100) DEFAULT NULL COMMENT 'Award notice date or Notice of Grant Award (NGA) is a legally binding document stating the government has obligated funds and which defines the period of support and the terms and conditions of award.',
                              `budget_start` varchar(100) DEFAULT NULL COMMENT 'The date when a project’s funding for a particular fiscal year begins.',
                              `budget_end` varchar(100) DEFAULT NULL COMMENT 'The date when a project’s funding for a particular fiscal year ends.',
                              `cfda_code` varchar(100) DEFAULT NULL COMMENT 'Federal programs are assigned a number in the Catalog of Federal Domestic Assistance (CFDA), which is referred to as the CFDA code. The CFDA database helps the Federal government track all programs it has domestically funded.',
                              `core_project_num` varchar(100) DEFAULT NULL COMMENT ' An identifier for each research project, used to associate the project with publication and patent records. This identifier is not specific to any particular year of the project. It consists of the project activity code, administering IC, and serial number (a concatenation of Activity, Administering_IC, and Serial_Number).',
                              `ed_inst_type` varchar(100) DEFAULT NULL COMMENT 'Generic name for the grouping of components across an institution who has applied for or receives NIH funding. The official name as used by NIH is Major Component Combining Name.',
                              `foa_number` varchar(100) DEFAULT NULL COMMENT 'The number of the funding opportunity announcement, if any, under which the project application was solicited.  Funding opportunity announcements may be categorized as program announcements, requests for applications, notices of funding availability, solicitations, or other names depending on the agency and type of program. Funding opportunity announcements can be found at Grants.gov/FIND',
                              `full_project_num` varchar(100) DEFAULT NULL COMMENT 'Commonly referred to as a grant number, intramural project, or contract number.  For grants, this unique identification number is composed of the type code, activity code, Institute/Center code, serial number, support year, and (optional) a suffix code to designate amended applications and supplements.',
                              `funding_ics` varchar(300) DEFAULT NULL COMMENT 'The NIH Institute or Center(s) providing funding for a project are designated by their acronyms (see Institute/Center acronyms).  Each funding IC is followed by a colon (:) and the amount of funding provided for the fiscal year by that IC.  Multiple ICs are separated by semicolons (;).  Project funding information is available only for NIH, CDC, FDA, and ACF projects.',
                              `funding_mechanism` varchar(100) DEFAULT NULL COMMENT 'The major mechanism categories used in NIH Budget mechanism tables for the President’s budget. Extramural research awards are divided into three main funding mechanisms: grants, cooperative agreements and contracts. A funding mechanism is the type of funded application or transaction used at the NIH. Within each funding mechanism NIH includes programs. Programs can be further refined by specific activity codes.',
                              `fy` int(11) DEFAULT NULL COMMENT 'The fiscal year appropriation from which project funds were obligated.',
                              `ic_name` varchar(100) DEFAULT NULL COMMENT 'Full name of the administering agency, Institute, or Center. ',
                              `nih_spending_cats` text COMMENT 'Congressionally-mandated reporting categories into which NIH projects are categorized.  Available for fiscal years 2008 and later.  Each project’s spending category designations for each fiscal year are made available the following year as part of the next President’s Budget request.  See the Research, Condition, and Disease Categorization System for more information on the categorization process.',
                              `org_city` varchar(100) DEFAULT NULL COMMENT 'The city in which the business office of the grantee organization or contractor is located.  Note that this may be different from the research performance site.  For all NIH intramural projects, Bethesda, MD is used.',
                              `org_country` varchar(100) DEFAULT NULL COMMENT 'The country in which the business office of the grantee organization or contractor is located.  Note that this may be different from the research performance site.',
                              `org_dept` varchar(100) DEFAULT NULL COMMENT 'The departmental affiliation of the contact principal investigator for a project, using a standardized categorization of departments. Names are available only for medical school departments.',
                              `org_district` int(11) DEFAULT NULL COMMENT 'The congressional district in which the business office of the grantee organization or contractor is located.  Note that this may be different from the research performance site.',
                              `org_duns` varchar(100) DEFAULT NULL COMMENT 'This field may contain multiple DUNS Numbers separated by a semi-colon. The Data Universal Numbering System is a unique nine-digit number assigned by Dun and Bradstreet Information Services, recognized as the universal standard for identifying and keeping track of business worldwide.',
                              `org_fips` varchar(100) DEFAULT NULL COMMENT 'The country code of the grantee organization or contractor as defined in the Federal Information Processing Standard.',
                              `org_ipf_code` int(11) DEFAULT NULL COMMENT 'The Institution Profile (IPF) number is an internal NIH identifier that uniquely identifies and associates institutional information within NIH electronic systems. The NIH assigns an IPF number after the institution submits its request for registration.',
                              `org_name` varchar(100) DEFAULT NULL COMMENT 'The name of the educational institution, research organization, business, or government agency receiving funding for the grant, contract, cooperative agreement, or intramural project.',
                              `org_state` varchar(100) DEFAULT NULL COMMENT 'The state in which the business office of the grantee organization or contractor is located.  Note that this may be different from the research performance site.',
                              `org_zipcode` int(11) DEFAULT NULL COMMENT 'The zip code in which the business office of the grantee organization or contractor is located.  Note that this may be different from the research performance site.',
                              `phr` text COMMENT 'Submitted as part of a grant application, this statement articulates a projects potential to improve public health.',
                              `pi_ids` varchar(300) DEFAULT NULL COMMENT 'A unique identifier for each of the project Principal Investigators. Each PI in the RePORTER database has a unique identifier that is constant from project to project and year to year, but changes may be observed for investigators that have had multiple accounts in the past, particularly for those associated with contracts or sub-projects.',
                              `pi_names` varchar(600) DEFAULT NULL COMMENT 'The name(s) of the Principal Investigator(s) designated by the organization to direct the research project.',
                              `program_officer_name` varchar(100) DEFAULT NULL COMMENT 'An Institute staff member who coordinates the substantive aspects of a contract from planning the request for proposal to oversight.',
                              `project_start` varchar(100) DEFAULT NULL COMMENT 'The start date of a project.  For subprojects of a multi-project grant, this is the start date of the parent award. ',
                              `project_end` varchar(100) DEFAULT NULL COMMENT 'The current end date of the project, including any future years for which commitments have been made.  For subprojects of a multi-project grant, this is the end date of the parent award.  Upon competitive renewal of a grant, the project end date is extended by the length of the renewal award. ',
                              `project_terms` text COMMENT 'Prior to fiscal year 2008, these were thesaurus terms assigned by NIH CRISP indexers.  For projects funded in fiscal year 2008 and later, these are concepts that are mined from the projects title, abstract, and specific aims using an automated text mining tool.',
                              `project_title` varchar(200) DEFAULT NULL COMMENT 'Title of the funded grant, contract, or intramural (sub)project.',
                              `serial_number` int(11) DEFAULT NULL COMMENT 'A six-digit number assigned in serial number order within each administering organization.  ',
                              `study_section` varchar(100) DEFAULT NULL COMMENT ' A designator of the legislatively-mandated panel of subject matter experts that reviewed the research grant application for scientific and technical merit.',
                              `study_section_name` varchar(200) DEFAULT NULL COMMENT 'The full name of a regular standing Study Section that reviewed the research grant application for scientific and technical merit.  Applications reviewed by panels other than regular standing study sections are designated by Special Emphasis Panel.',
                              `subproject_id` varchar(100) DEFAULT NULL COMMENT 'A unique numeric designation assigned to subprojects of a `parent` multi-project research grant.',
                              `suffix` varchar(100) DEFAULT NULL COMMENT 'A suffix to the grant application number that includes the letter `A` and a serial number to identify an amended version of an original application and/or the letter `S` and serial number indicating a supplement to the project.',
                              `support_year` int(11) DEFAULT NULL COMMENT 'The year of support for a project, as shown in the full project number.  For example, a project with number 5R01GM0123456-04 is in its fourth year of support.',
                              `direct_cost_amt` varchar(100) DEFAULT NULL COMMENT ' Total direct cost funding for a project from all NIH Institute and Centers for a given fiscal year. Costs are available only for NIH awards funded in FY 2012 onward. Direct cost amounts are not available for SBIR/STTR awards.',
                              `indirect_cost_amt` varchar(100) DEFAULT NULL COMMENT 'Total indirect cost funding for a project from all NIH Institute and Centers for a given fiscal year. Costs are available only for NIH awards funded in FY 2012 and onward. Indirect cost amounts are not available for SBIR/STTR awards.',
                              `total_cost` varchar(100) DEFAULT NULL COMMENT 'Total project funding from all NIH Institute and Centers for a given fiscal year.',
                              `total_cost_sub_project` varchar(100) DEFAULT NULL COMMENT 'Applies to subproject records only. Total funding for a subproject from all NIH Institute and Centers for a given fiscal year. Costs are available only for NIH awards.',
                              `source` varchar(200) DEFAULT NULL COMMENT 'The source of this information.',
                              `version` int(11) NOT NULL DEFAULT '0' COMMENT 'The version of the data pulled from the `source`',
                              PRIMARY KEY (`application_id`,`version`),
                              KEY `projects_core_project_num_index` (`core_project_num`),
                              KEY `projects_total_cost_index` (`total_cost`),
                              FULLTEXT KEY `projects_project_title_index` (`project_title`),
                              FULLTEXT KEY `projects_project_terms_index` (`project_terms`)
                            ) ENGINE=InnoDB DEFAULT CHARSET=latin1                
            """

        self.log(' Creating ExPORTER Tables...')
        for table, create_table in create_table_queries.items():

            # if table != 'patents':
            #    continue

            # If we've asked to replace the table, or if this is patents
            if replace:
                self.log('....dropping', table)
                drop_table = """DROP TABLE IF EXISTS {table}""".format(table=table)
                self.db.query(drop_table)
                self.log('...creating', table)
                self.db.query(create_table)
            else:
                self.log('...Creating Table `' + table + '`')
                self.db.query(create_table)

    def get_files_already_inserted(self, table):
        """ For each table, get a list of all files already used as sources """
        self.debug("Getting files already inserted...")
        sources = []
        rows = self.db.query(f"""SELECT DISTINCT source FROM {table}""")
        if rows:
            sources += [row['source'] for row in rows]
            self.debug(f"{len(rows)} files already inserted.")
        return sources

    def characterizeData(self, replace_existing, limit_to_tables):
        """
        ################################################################################################
        # This Function characterizes the ExPORTER Data Download and stores the results in ExPORTER/stats/
        # -----------------------------------------------------------------------------------------------
        # INPUTS
        # replace_existing    <Bool>   - When True, all previously downloaded files are replaced.
        # -----------------------------------------------------------------------------------------------
        # OUTPUTS
        # See ExPORTER/stats/ for a set of files that characterize the downloaded data.
        ################################################################################################
        """
        folder_path = glob.glob(f"{self.save_directory}/*")

        self.log('------------------------------------------------')
        self.log(' Characterizing ExPORTER Data                   ')
        self.log('------------------------------------------------')

        # ----------------------------------------------
        # For each folder of data...
        # ----------------------------------------------
        for folder in folder_path:

            # Get the folder name
            folder_name = folder.split('/')[-1]
            if '.' in folder_name:
                folder_name = '.'.join(folder_name.split('.')[:-1])

            if limit_to_tables != []:
                if folder_name not in limit_to_tables:
                    continue

            # Get the data path
            data_path = glob.glob(folder + '/json/*')
            data_info = {}

            # We do not want to do anything with the data statistics
            if folder_name == 'stats':
                continue

            self.log('Processing', folder, '...')

            # Figure out which files we have already computed stats for
            stats_computed = [folder.split('/')[-1] for folder in
                              glob.glob(f'{self.save_directory}/stats/*')]
            this_stat_name = folder_name + '.json'
            if (this_stat_name in stats_computed) and (replace_existing == False):
                self.log('.... Skipping - stats were previously computed')
                continue
            else:
                self.log('.... Computing stats - this may take a while')

            # ----------------------------------------------
            # For each data file in the folder...
            # ----------------------------------------------
            for data in data_path:
                data_name = data.split('/')[-1]
                data_name = '.'.join(data_name.split('.')[:-1])

                # ----------------------------------------------
                # For each line in the data file...
                # ----------------------------------------------
                with open(data) as f:
                    for line in f:

                        json_line = json.loads(line)

                        # ----------------------------------------------
                        # Get the line statistics
                        # ----------------------------------------------
                        for real_key, val in json_line.items():

                            key = real_key.lower().replace(' ', '_').replace('.', '_')

                            # -----------------------------------------------
                            # If this is a new key, add it to the dict
                            # -----------------------------------------------
                            if data_info.get(key) == None:
                                data_info[key] = {'max_value_size': 0,
                                                  'data_type': {'INT': 0,
                                                                'VARCHAR': 0,
                                                                'FLOAT': 0,
                                                                'DATE': 0
                                                                },
                                                  'column_name': ''
                                                  }

                            # ----------------------------------------------
                            # Generate the column name from he key
                            # -----------------------------------------------
                            if data_info[key]['column_name'] == '':
                                data_info[key]['column_name'] = key.lower().replace(' ', '_').replace('.', '_')

                            # -----------------------------------------------
                            # Get the max_value_size
                            # -----------------------------------------------
                            if val is not None:
                                if data_info[key]['max_value_size'] < len(val):
                                    data_info[key]['max_value_size'] = len(val)

                            # -----------------------------------------------
                            # Get the data_type
                            # -----------------------------------------------
                            if val is not None:
                                if representsInt(val):
                                    data_info[key]['data_type']['INT'] += 1
                                elif representsFloat(val):
                                    data_info[key]['data_type']['FLOAT'] += 1
                                elif representsDatetime(val, fuzzy=False):
                                    data_info[key]['data_type']['DATE'] += 1
                                else:
                                    data_info[key]['data_type']['VARCHAR'] += 1

            # -----------------------------------------------------
            # Saving Batch
            # -----------------------------------------------------
            if not os.path.isdir('data/ExPORTER/stats'):
                os.mkdir('data/ExPORTER/stats')

            outfile = open('data/ExPORTER/stats/' + folder_name + '.json', "w")
            json.dump(data_info, outfile)
            outfile.close()

    def request(self, replace_existing, limit_to_tables):
        """
        # This Function collects files pasted on the NIH ExPORTER website
        #-----------------------------------------------------------------------------------------------
        # INPUTS
        # save_directory      <String> - Indicates the directory where we will save the downloaded data.
        # replace_existing    <Bool>   - When True, all previously downloaded files are replaced.
        #-----------------------------------------------------------------------------------------------
        # OUTPUTS
        # See the ExPORTER/ directory for information on the files
        """
        # For each of the Exporter tabs
        self.log('Downloading data from https://reporter.nih.gov/. Files will be saved to', self.save_directory)

        # URLs at which to find all the files for each table
        table_urls = {
            'abstracts': [f"{self.base_url}/Download?fileId={i}" for i in list(range(1, 72, 2))+[335] ],  # 1, 3, 5, ..., 69, 71, 335
            'projects': [f"{self.base_url}/Download?fileId={i}" for i in list(range(2, 73, 2))+[334] ],  # 2, 4, 6, ..., 70, 72, 334
            'link_tables': [f"{self.base_url}/Download?fileId={i}" for i in list(range(154, 113, -1))+[337] ],  # 154, 153, ..., 115, 114, 337
            'publications': [f"{self.base_url}/Download?fileId={i}" for i in list(range(73, 114))+[336] ],   # 73, 74, ..., 112, 113, 336
            'patents': [f"{self.base_url}/DownloadFile?groupName=PATENT"],
            'clinical_studies': [f"{self.base_url}/DownloadFile?groupName=CLINICALSTUDY"]
        }

        for index, table in enumerate(limit_to_tables):
            self.log("\nTable:", table)

            table_directory = f"{self.save_directory}/{table}"  # directory for all files related to this table
            raw_directory = f"{table_directory}/raw"  # where to save the raw zip files
            self.debug(f"Raw directory: {raw_directory}")
            if not os.path.isdir(raw_directory):
                self.debug("Raw directory not found - creating it")
                os.makedirs(raw_directory)
            else:
                self.debug("Raw directory already exists")

            # remove existing file if specified (and for some files, we will always want to replace existing)
            if replace_existing or table in ['patents', 'clinical_studies']:
                if os.path.isdir(table_directory):
                    shutil.rmtree(table_directory)  # remove these directories

            # To keep track of new files we've added to the collection
            newly_downloaded_files = 0
            previously_downloaded_files = 0

            # For each file URL
            urls = table_urls[table]  # file urls for this table
            for url in urls:
                time.sleep(0.5)  # be nice
                self.log("Requesting... ", end='')
                self.mark_time('r')

                # Use curl because for some reason requests.get() takes forever (are they rate limiting somehow??)
                # -s: silent
                # -D: output only the received headers, and "-" redirects to stdout (which we read into header_text)
                # -o: dump body to file
                header_text = os.popen(f"curl {url} -s -D - -o {self.temp}").read()

                search = re.search('Content-Disposition:.*filename=(.*?\.zip)', header_text, re.IGNORECASE)
                # TODO: patents download is a raw CSV, not a zip
                if not search:  # no regex match
                    self.log(f"Error - filename not found in response. URL: {url}")
                    continue

                filename = search.group(1)

                self.add_time('r')
                self.log(f" {filename} ({self.get_time_last('r')})", end='')
                
                # The publications are special in that they also contain author affiliation files.
                if (table == 'publications') and ('_AFFLNK_' in filename):
                    table = 'affiliations'
                if (table == 'affiliations') and ('_AFFLNK_' not in filename):
                    table = 'publications'
                
                # These appendices are not applicable
                if table == 'projects':
                    if ('_DUNS_' in filename) or ('_PRJFUNDING_' in filename):
                        self.log(" ...discarded")
                        continue

                # move file to raw directory if it's a new one
                file_path = f"{raw_directory}/{filename}"
                if not replace_existing and os.path.exists(file_path):
                    previously_downloaded_files += 1
                    self.log(" ...already downloaded")
                    continue
                else:
                    os.popen(f"mv {self.temp} {file_path}")
                    self.log(" ...downloaded.")
                    newly_downloaded_files += 1

            # Display download statistics to the users
            self.log(f"Done Collecting {self.get_time_total('r')}")
            self.log(f"Previously downloaded: {previously_downloaded_files}")
            self.log(f"Newly downloaded: {newly_downloaded_files}")

    def unpack_data(self, replace, tables):
        """ Unzip and JSONify the downloaded data """
        self.mark_time('t')
        self.log('\nUnpacking Data....')
        # For each of the subdirectories in the save_directory
        paths = glob.glob(f"{self.save_directory}/*")
        for path in paths:

            table = path.split('/')[-1]
            if table not in tables:
                self.log("\nSkipping: ", table)
                continue
            self.log(f"\n{table}:")

            # directory to store unzipped csv file
            csv_directory = f"{path}/unzipped"
            os.makedirs(csv_directory, exist_ok=True)

            # directory to store parsed JSON files
            json_directory = f"{path}/json"
            os.makedirs(json_directory, exist_ok=True)

            # For each of the .zip files in the raw directory
            raw_file_paths = glob.glob(f"{path}/raw/*.zip")
            for file in raw_file_paths:
                filename = file.split('/')[-1]
                filename = '.'.join(filename.split('.')[:-1])
                self.log(f"{filename} ... ", end='')
                self.mark_time('f')

                json_path = f"{json_directory}/{filename}.jsonl"

                # Extract all the contents of zip file to the csv directory
                with ZipFile(file, 'r') as zipObj:
                    extracted_file_name = zipObj.namelist()[0]
                    csv_path = f"{csv_directory}/{extracted_file_name}"  # path to the unzipped csv file
                    if not replace and os.path.exists(csv_path):  # skip if already unzipped
                        self.log(" already exists")
                        continue
                    zipObj.extractall(path=csv_directory)  # unzip to the csv directory

                # convert to JSON
                line_errors = self.parse_jsonl(csv_path, json_path)
                self.add_time('f')
                self.log(f" done {self.get_time_last('f')} Errors: {line_errors}")

            self.add_time('t')
            self.log("Table Complete.", self.get_time_last('t'))

        self.log("Unpacking Data Complete.", self.get_time_total('t'))
        self.clear_time('t')

    def parse_jsonl(self, csv_path, json_path):
        """ Given the path to csv file, convert it to JSONL and store it at json_path """
        # Get the year from the file name
        year = findMatches("[0-9]{4}", csv_path)
        year = None if year == [] else year[0]

        line_import_errors = 0

        with open(csv_path, 'r', errors='replace') as f:
            json_lines, count = [], 0
            for line in reader(f):  # iterate through each line using a CSV reader
                count += 1
                if count == 1:  # If this is the first line, this is a header.
                    headers = line
                    continue

                # Check for errors
                if len(headers) != len(line):
                    line_import_errors += 1
                    continue

                # Package the line as JSON
                json_line = {'year': year}
                for i, header in enumerate(headers):
                    json_line[header] = line[i]
                json_lines.append(json_line)

        # save json to disk
        # Open the JSON output file in append mode
        with open(json_path, "a") as outfile:
            for line in json_lines:
                json.dump(line, outfile)
                outfile.write('\n')

        return line_import_errors

    def import_data(self, replace_existing, limit_to_tables, batch_size = 5000):
        """
        ################################################################################################
        # Imports the data from json files into the database
        #-----------------------------------------------------------------------------------------------
        # INPUTS
        # replace_existing    <Bool>   - When True, all previously downloaded files are replaced.
        # exlcude_data        <list>   - the list of tables you want to ignore.
        #-----------------------------------------------------------------------------------------------
        # OUTPUTS
        # When this function is complete, the data will have loaded into the database.
        ################################################################################################
        """
        #skip_until = 'RePORTER_PRJABS_C_FY1991'
        #skip_flag = True
        self.log(f'Importing Data into Database from: {self.save_directory}')
         
        folder_path = glob.glob(f"{self.save_directory}/*")
        errors = 0

        # For each folder of data
        for folder in folder_path:
            # Get the folder name
            table = folder.split('/')[-1]
            if '.' in table:
                table = '.'.join(table.split('.')[:-1])

            if table not in limit_to_tables:
                self.log("\nSkipping: ", table)
                continue
            self.log(f"\nImporting data into: {table}")

            # Get the data path
            data_path = glob.glob(folder + '/json/*')
            
            # Sort the data_path
            data_list = [d.split('/')[-1].lower() for d in data_path]
            sindex    = list(np.argsort(data_list))
            data_paths = [data_path[sindex[i]] for i in range(len(data_path))]
            #print(data_path)
            #data_path.reverse()

            # Get the information on the table we want to insert into
            table_info = self.db.getTableInfo(table)

            # If this is the patents table, everything must be wiped.
            if table == 'patents':
                self.log('Deleting patents - these records are replaced, not augmented...')
                self.db.query("DELETE FROM patents")

            files_already_inserted = self.get_files_already_inserted(table)

            # For each data file in the folder...
            for data in data_paths:
                # Get the name of the data file.
                data_name = data.split('/')[-1]
                data_name = '.'.join(data_name.split('.')[:-1])
                
                # Get the version number of the data
                if (data_name.split('_')[-1][0:2] == 'FY' ) or (data_name.split('_')[-1] == 'new') or  (data_name.split('_')[-1].lower() == 'all'):
                    version_number = 0
                else:
                    version_number = int(data_name.split('_')[-1])
                        
                # Let's see if this data exists or not: 
                if (data_name in files_already_inserted) and not replace_existing:
                    self.log('...Skipping', data_name)
                    continue
                else:
                    self.log(f'...Importing "{data_name}" ', end='')

                self.mark_time('t')
                query_result = None  # async query result
                with open(data) as f:
                    query_values = ''
                    parameters    = []
                    for ii, line in enumerate(f):  # For each line in the data file...
                        json_line = json.loads(line)

                        #----------------------------------------------
                        # Get the line statistics
                        #----------------------------------------------
                        keys, values  = '', ''
                        for real_key, value in json_line.items():
                            # Get the Keys
                            key = real_key.lower().replace(' ','_').replace('.','_')

                            # Get the data type
                            if table_info.get(key):
                                data_type = table_info.get(key)['data_type']
                            else:
                                data_type = None

                            # If this is an int/float, cast non-friendly data to None
                            if data_type == 'int' and not representsInt(value):
                                value = None
                            elif data_type is None:
                                value = None

                            if value == '':
                                value = None

                            if value is not None: 
                                value = value.encode("ascii", "ignore")

                            # If this is a date, parse to SQL format
                            if data_type == 'date':
                                try:
                                    value = parse(value, fuzzy=False)
                                except:
                                    errors += 1
                                    value = None

                            parameters.append(value)
                            values    += '%s' + ',' 
                            keys      += key  + ','
                        
                        # Finish off by noting the source
                        keys       += 'source' + ','
                        values     += '%s'     + ','
                        parameters += [data_name]
                        
                        #... and the version number
                        keys       += 'version'
                        values     += '%s'
                        parameters += [version_number]
                        
                        query_values += f"""({values}),"""
                        
                        # Insert the batch of data
                        if query_result is not None:
                            query_result.wait()  # wait for previous query
                        if ((ii % batch_size) == 0) and (ii != 0):
                            query = """INSERT IGNORE INTO {table_name} ({keys}) 
                                       VALUES {query_values}""".format(table_name = table, keys = keys, query_values = query_values[:-1])
                            query_result = self.db.query(query,parameters, threaded=True)
                            query_values = ''
                            parameters   = []

                    # Insert the last batch
                    if query_result is not None:
                        query_result.wait()  # wait for previous query
                    if query_values != '':
                        query = """INSERT IGNORE INTO {table_name} ({keys}) 
                                    VALUES {query_values}""".format(table_name = table, keys = keys, query_values = query_values[:-1])
                        self.db.query(query,parameters)

                self.add_time('t')
                self.log(f"...done {self.get_time_last('t')}")

        self.log("Data Import Complete. ", self.get_time_total('t'))
        self.clear_time('t')