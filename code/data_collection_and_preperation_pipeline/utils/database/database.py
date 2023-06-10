import os, sys
from mysql.connector.pooling import MySQLConnectionPool
from mysql.connector.errors import PoolError
import redshift_connector

from multiprocessing.pool import ThreadPool
from datetime import date
from time import time, sleep
import itertools

from configuration.config import Config, RedshiftWarehouseConfig, MysqlDatabaseConfig
from utils.base import Base


class Database(Base):
    """ Base class which handles a connection to a database """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # dump file prefix
        self.dump_prefix = "dump_" if self.config.debug else "dump_"

    def query(self, query, parameters=None, format='cols', threaded=False):
        """ Customized by SQL flavor subclasses """
        pass


class MySQLDatabase(Database):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.database = self.config.mysql.database
        self.host = self.config.mysql.host
        self.port = self.config.mysql.port or 3306
        self.user = self.config.mysql.user
        self.password = self.config.mysql.password
        self.debug(f"MySQL URL: \"{self.host}:{self.port}/{self.database}\"")
        self.debug(f"MySQL Credentials: Username: \"{self.user}\", Password: \"{self.password}\"")

        # thread pool for parallel queries
        self.threads = min(self.config.mysql.threads, 32)  # limit threads at 32
        self.thread_pool = ThreadPool(self.threads)

        self.connection_pool = MySQLConnectionPool(
            pool_name="mypool",
            pool_size=self.threads,
            host=self.host,
            user=self.user,
            password=self.password,
            port=self.port,
            database=self.database
        )

    def get_connection(self):
        """ Get a connection from the pool """
        while True:
            try:
                return self.connection_pool.get_connection()
            except PoolError:  # no connections available
                self.log("No database connections available in the pool - waiting")
            sleep(1)

    def query(self, query, parameters=None, format='cols', threaded=False):
        """
        <format> of the returned results:
            "rows": list of rows, where each row is a dictionary of column names and values
            "cols": Dictionary of columns, where each column is a list of row values.
        If <threaded> is True, returns an AsyncResult.
            Use result.wait() to block until the result is ready.
            Use result.get() to block and return the query result.
        """
        if threaded:  # run query in a new thread
            return self.thread_pool.apply_async(self.query, [query, parameters])  # call this function asynchronously

        cnx = self.get_connection()
        cnx.sql_mode = ''  # remove all sql modes
        cur = cnx.cursor(dictionary=True)

        try:
            if parameters is not None:
                cur.execute(query, parameters)
            else:
                cur.execute(query)

            # Fetch the result
            row = cur.fetchall()
            cnx.commit()

            cur.close()
            cnx.close()
            return row

        except Exception as e:
            try:
                self.log(f"Database Error. {e.__class__.__name__}: {e}")
                self.debug("[query]: \n", query)
                cur.close()
                cnx.close()
            except Exception as e:
                self.log("Failed to close connection after exception handled.")

    def insert_row(self, table, columns, parameters, threaded=False, db_insert=True):
        """
        Insert data into the database.
        <table> table name
        <columns> column names
        <parameters> list of values, or a list of lists of values for each row inserted.
        <threaded> if True, runs in a separate thread and returns an AsyncResult. Call result.get() to block and get the result.
        <db_insert> is whether to actually insert the data. Useful for debugging.
        """
        if not len(columns):
            self.debug("No rows inserted - no columns provided")
            return
        if not len(parameters):
            self.debug("No rows inserted - no parameters provided")
            return

        # Check if there are multiple rows present in the parameters
        has_multiple_rows = any(isinstance(el, list) for el in parameters)

        # Construct the query we will execute to insert the row(s)
        keys       = ','.join(columns)
        values     = ','.join(['%s' for x in columns])
        query = f"""INSERT IGNORE INTO {table} ({keys}) VALUES """
        if has_multiple_rows:
            for _ in parameters:
                query += f"""({values}),"""
            query     = query[:-1]
            parameters = list(itertools.chain(*parameters))
        else:
            query += f"""({values}) """

        # Indicates if we should skip the insert - this is useful for testing things.
        if db_insert == False:
            self.debug(f"[Database insertion disabled] Query would submit here. Parameters: {len(parameters)}")
            self.debug(f"Query: {query[:50]}{'...' if len(query)>50 else ''}")
            def simulate_query(): sleep(1)
            return self.thread_pool.apply_async(simulate_query)  # simulate an insert

        return self.query(query, parameters, threaded=threaded)

    def getTableInfo(self, table_name=None):
        """ Given a table name, return certain information about each column (data type, key, etc.) """
        table_info = {}
        if table_name is None:
            tables = [table['Tables_in_brainworks'] for table in self.query("SHOW TABLES")]
        else:
            tables = [table_name]
        
        # Get the columns
        for t in tables:
            query = """SELECT COLUMN_NAME,
                              DATA_TYPE,
                              COLUMN_COMMENT,
                              CHARACTER_MAXIMUM_LENGTH,
                              COLUMN_KEY
                         FROM information_schema.columns 
                        WHERE table_schema = '{database_name}' 
                          AND table_name   = '{table_name}'
                    """.format(table_name=t, database_name=self.database)
            results = self.query(query)
            column_info = {}
            for row in results:
                column_info[row['COLUMN_NAME']] = {}
                column_info[row['COLUMN_NAME']]['data_type'] = row['DATA_TYPE']
                column_info[row['COLUMN_NAME']]['column_length'] = row['CHARACTER_MAXIMUM_LENGTH']
                column_info[row['COLUMN_NAME']]['comment'] = row['COLUMN_COMMENT']
                column_info[row['COLUMN_NAME']]['column_key'] = row['COLUMN_KEY']
            table_info[t] = column_info
        
        if table_name is None:
            self.table_info = table_info
            return table_info
        else:
            return column_info

    def redshift_to_mysql_type(self, info):
        """ convert a MySQL type string into a RedShift type string """
        data = info['data_type']
        length = info['length']
        if data == "integer":
            return "INT"
        if data == "float":
            return "FLOAT"
        if data == "character varying":
            return f"VARCHAR({length})"
        if data == "bool":
            return "BOOL"
        if data == 'date':
            return "DATE"

    def dump_to_bucket(self, tables=None):
        """ Dump the selected tables (or all if None) to the S3 bucket """
        if tables is None:
            rows = self.query("SHOW TABLES")
            k = list(rows[0].keys())[0]
            tables = [r[k] for r in rows]
        self.log("Dumping tables from Aurora to S3 bucket: ", tables)

        for table in tables:
            self.log(f"\nDumping Table: {table} ... ")
            query = f"""
                SELECT * INTO OUTFILE S3 's3://{self.config.s3_bucket}/{self.dump_prefix}{table}'
                    CHARACTER SET utf8mb4
                    FORMAT CSV
                    MANIFEST ON
                    OVERWRITE ON
                FROM {table};
            """
            self.mark_time('t')
            self.query(query)
            self.add_time('t')
            self.log(f"Done {self.get_time_last('t')}")

        self.log("All tables dumped. ", self.get_time_total('t'))

    def load_from_bucket(self, tables):
        """ Load tables from S3 """
        self.log("Loading tables from S3 bucket...")
        self.mark_time('t')

        rdb = RedShiftDatabase(self.config)
        for table in tables:
            self.log(f"Creating table: {table}")

            info = rdb.getTableInfo(table)
            column_defs = []  # redshift column definitions
            for name, data in info.items():
                t = self.redshift_to_mysql_type(data)
                column_defs.append(f"{name} {t}")
            column_defs = ',\n'.join(column_defs)

            self.query(f"CREATE TABLE IF NOT EXISTS {table} ({column_defs})")
            self.query(f"TRUNCATE TABLE {table}")  # truncate if already exists

            self.log(f"Loading table: {table}")
            query = f"""
                LOAD DATA FROM S3 MANIFEST 's3://{self.config.s3_bucket}/{self.dump_prefix}{table}.manifest'
                INTO TABLE CUSTOMER
                FIELDS TERMINATED BY ','
                LINES TERMINATED BY '\n';
            """
            self.query(query)
            self.add_time('t')
            self.log(f"done {self.get_time_last('t')}")
        self.log(f"All tables loaded. {self.get_time_total('t')}")

class RedShiftDatabase(Database):
    def __init__(self, *args, **kwargs):
        Database.__init__(self, *args, **kwargs)

        self.database = self.config.redshift.database
        self.host = self.config.redshift.host
        self.port = self.config.redshift.port or 5439
        self.user = self.config.redshift.user
        self.password = self.config.redshift.password
        self.debug(f"RedShift URL: \"{self.host}:{self.port}/{self.database}\"")
        self.debug(f"RedShift Credentials: Username: \"{self.user}\", Password: \"{self.password}\"")

        # thread pool for parallel queries
        self.threads = min(self.config.redshift.threads, 32)  # limit threads at 32
        self.thread_pool = ThreadPool(self.threads)

        self.connection_keywords = {
            'host': self.host,
            'database': self.database,
            'user': self.user,
            'password': self.password,
            'port': self.port
        }

    def query(self, query, parameters=None, format='rows', threaded=False):
        """
        <format> of the returned results:
            "rows": list of rows, where each row is a dictionary of column names and values
            "cols": Dictionary of columns, where each column is a list of row values.
        If <threaded> is True, returns an AsyncResult.
            Use result.wait() to block until the result is ready.
            Use result.get() to block and return the query result.
        """
        if threaded:  # run query in a new thread
            self.debug("Threaded RedShift query.")
            return self.thread_pool.apply_async(self.query, [query, parameters, format])  # call this function asynchronously

        # Connect to the cluster
        conn = redshift_connector.connect(**self.connection_keywords)

        cur = conn.cursor()
        cur.execute(query, parameters)

        if cur.description:
            keys = [tup[0] for tup in cur.description]  # return column keys
            raw_rows = cur.fetchall()
            conn.commit()
            cur.close()
            conn.close()

            if format == 'cols':
                columns = {k: [] for k in keys}
                for row in raw_rows:
                    for i, key in enumerate(keys):
                        columns[key].append(row[i])
                return columns
            else:  # rows
                rows = []
                for row in raw_rows:
                    rows.append({keys[i]: row[i] for i in range(len(keys))})
                return rows


        else:
            conn.commit()
            cur.close()
            conn.close()

    def mysql_to_redshift_type(self, info):
        """ convert a MySQL type string into a RedShift type string """
        data = info['data_type']
        length = info['column_length']
        if data in ["int", "bigint", "bool", "date"]:
            return data
        if data == "float":
            return "FLOAT8"
        if data in ["text", "varchar"]:
            return f"VARCHAR({length})"

    def getTableInfo(self, tables):
        """ Given a table name, return certain information about each column (data type, key, etc.) """
        if not type(tables) == list:
            tables = [tables]

        table_info = {}
        for table in tables:
            query = f"""
                SELECT
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM SVV_COLUMNS
                WHERE table_catalog = '{self.database}'
                AND table_name = '{table}'
            """
            results = self.query(query)

            column_info = {}
            for row in results:
                name = row['column_name']
                column_info[name] = {
                    "data_type": row["data_type"],
                    "length": row['character_maximum_length'],
                    "nullable": row['is_nullable'],
                    "column_default": row['column_default']
                }

            table_info[table] = column_info

        return table_info

    def dump_to_bucket(self, tables):
        """ Dump tables to an S3 bucket """
        self.log("Dumping tables from RedShift to S3 bucket: ", tables)

        for table in tables:
            self.log(f"\nDumping Table: {table} ... ")
            query = f"""
                UNLOAD ('SELECT * FROM {table}')
                TO 's3://{self.config.s3_bucket}/{self.dump_prefix}{table}'
                iam_role '{self.config.redshift.iam_s3_access_role}'
                CSV MANIFEST ALLOWOVERWRITE;
            """
            self.mark_time('t')
            self.query(query)
            self.add_time('t')
            self.log(f"Done {self.get_time_last('t')}")

        self.log("All tables dumped. ", self.get_time_total('t'))

    def load_from_bucket(self, tables):
        """
        Load tables from S3 bucket.
        Columns must be the output from a getTableInfo() call
        """
        self.log("Loading tables from S3 bucket...")
        self.mark_time('t')

        mdb = MySQLDatabase(self.config)
        for table in tables:
            self.log(f"Creating table: {table}")

            info = mdb.getTableInfo(table)
            column_defs = []  # redshift column definitions
            for name, data in info.items():
                t = self.mysql_to_redshift_type(data)
                column_defs.append(f"{name} {t}")
            column_defs = ',\n'.join(column_defs)

            self.query(f"CREATE TABLE IF NOT EXISTS {table} ({column_defs})")
            self.query(f"TRUNCATE TABLE {table}")  # truncate if already exists

            self.log(f"Loading table: {table}")
            query = f"""
                COPY {table}
                FROM 's3://{self.config.s3_bucket}/{self.dump_prefix}{table}.manifest' 
                iam_role '{self.config.redshift.iam_s3_access_role}'
                CSV MANIFEST;
            """
            self.query(query)
            self.add_time('t')
            self.log(f"done {self.get_time_last('t')}")
        self.log(f"All tables loaded. {self.get_time_total('t')}")

