import mysql.connector
from flask import current_app as app
import logging

class database:
    def __init__(self, use_local = False):
        # Grab information from the configuration file
        self.use_local      = use_local
        self.local_db       = False
        self.database       = app.config['BRAINWORKS_DB_DATABASE']
        self.host           = app.config['BRAINWORKS_DB_HOST']
        self.user           = app.config['BRAINWORKS_DB_USER']
        self.port           = app.config['BRAINWORKS_DB_PORT']
        self.password       = app.config['BRAINWORKS_DB_PASSWORD']

    def check_database(self):
        # ----------------------------------------------------------
        # Checks if database is online/offline, returns false if offline
        # ----------------------------------------------------------
        return False

    def query(self, query="SELECT CURDATE()", parameters=None, use_local = False, show=False):

        # ----------------------------------------------------------
        # If this is a local instance of the database.
        # ----------------------------------------------------------
        if (self.local_db is True) or (self.use_local == True):
            if self.database == None:
                cnx = mysql.connector.connect(option_files=self.option_files) # Connect to server
            else:
                cnx = mysql.connector.connect(option_files=self.option_files, database=self.database) # Connect to server
        # ----------------------------------------------------------
        # If this is a remote instance of the database.
        # ----------------------------------------------------------
        else:
            cnx = mysql.connector.connect(host     = self.host,
                                          user     = self.user,
                                          password = self.password,
                                          port     = self.port,
                                          database = self.database
                                         )

        cur = cnx.cursor(dictionary=True)
        if parameters is not None:
            cur.execute(query, parameters)
        else:
            cur.execute(query)

        # Fetch one result
        row = cur.fetchall()
        cnx.commit()

        if "INSERT" in query:
            cur.execute("SELECT LAST_INSERT_ID()")
            row = cur.fetchall()
            cnx.commit()
        cur.close()
        cnx.close()
        return row