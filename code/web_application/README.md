# BRAINWORKS

This repository contains the website for the BRAINWORKS project.

This documentation necessarily assumes knowledge of AWS services, Linux server management, Git, Python, Python Flask, Gunicorn, NginX, SQL database management, and networking infrastructure.

To build the project on a Linux server, run bash script `./setup.sh`. This will install all necessary dependencies and start serving with nginx and gunicorn.

## How to configure
All configuration options should be located in `./config.py`, which is not included in the repository for security purposes.
Use the following commands to create this configuration file from the template:
```
cd brainworks-website
cp config_template.py config.py
```
For a website using RedShift SQL as a backend, the RedShiftConfig will be used. Below is a description of each configuration option\
`DOMAIN_NAME` The URL or IP address used to access the website. If you have a registered domain using SSL, you must include the "https://" portion.\
`SESSION_COOKIE_SECURE` Do not change\
`SESSION_COOKIE_SAMESITE` Do not change

The following parameters are for the website user database, which by default look for values in environment variables.\
`user` User database username\
`password` User database password\
`host` User database hostname\
`port` User database port\
`database` User database name

`SQLALCHEMY_DATABASE_URI` This is the full URI of the local user database being used. If the above parameters are set, this can be set to `f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"` to connect to a local MySQL database. This is recommended if the website is public-facing. Otherwise, you can instead set this to `"sqlite:///../local/database.db"` to use a local SQLite file as a user database for a simpler setup.

The following parameters are for the main BRAINWORKS database\
`DATA_DATABASE` What type of database is being used. Either "MYSQL" or "REDSHIFT"\
`BRAINWORKS_DB_DATABASE` Name of the database\
`BRAINWORKS_DB_HOST` Database hostname\
`BRAINWORKS_DB_USER` Database username\
`BRAINWORKS_DB_PORT` Database port. For RedShift this is 5439 by default\
`BRAINWORKS_DB_PASSWORD` Database password

The following parameters should only be set it you have properly configured an AWS Simple Email Service. This allows the platform to send emails to users for email validation, password reset, etc.\
`EMAIL` Bollean - whether to enable email sending.\
`NEVERBOUNCE_KEY` API key for [Neverbounce](https://neverbounce.com/). This service is used to validate emails.\
`AWS_REGION` AWS region for the account with access to the SES\
`EMAIL_ACCESS_KEY` AWS account access key ID\
`EMAIL_SECRET_KEY` AWS account access key\
`EMAIL_ADDRESS` SES email to send from



## How to run
This website uses NginX, Gunicorn, and Python Flask to run. NginX acts as a reverse proxy to gunicorn, which serves the Flask app.
To start guncicorn, use the following commands after connecting to the remote server via SSH:

```
cd brainworks-website
. venv/bin/activate
nohup gunicorn -c gunicorn_config.py &
```

Then run NginX (if it is not already) using the following command. Note that we are using a custom nginx configuation file located in the repository.
```
nginx -c /user/ubuntu/brainworks-public/nginx.conf
```

If NginX is already running using the default nginx configuration, you will need to first stop it using `sudo systemctl stop nginx`

## How to create an admin user
To create an administrator for the website, you must first create a regular account. Once you have done that, run the following commands after connecting to the remote server via SSH (using the email of the account you wish to make an admin):
```
cd brainworks-website
. venv/bin/activate
python3 set_admin.py email_of_user@email.com
```

Once an Admin user has been created, this account can be used to promote other users to Management users via the website interface itself. Management users have all the same privileges as Admin users, except the ability to manage other Management users.

## How to make public-facing
If you have a registered domain name with SSL, follow the instructions for using Certbot [here](https://certbot.eff.org/instructions?ws=nginx&os=ubuntufocal).
You will need to properly configure nginx to serve your SSL certificate. Follow [these](https://nginx.org/en/docs/http/configuring_https_servers.html) instructions to do so. Note that the nginx configuration is located in `./nginx.conf`

# Development instructions

## React Documentation

[React - Structure / Style](#react-structure-and-style-guide)

[React - Adjusting the Tools](#installation)

# Installation

This application uses React v18 as the front end and Flask as the back end.

## React Installation

This is a React Typescript application using Redux for state management and Chakra UI for styling.

Prerequisites: [NodeJS](https://nodejs.org/en/)

Navigate to the `react-app` folder, from the `brainworks-flask-app` folder do

```
cd react-app
```

Install the needed NPM packages

```
npm install
```

Start the application in development mode

```
npm start
```

The React application should now be running

- To learn about the structure and design of the React application, please read: [React - Key features](#installation)
- To learn about adjusting the create tool, please read:

## Flask Installation

Written by @ghamutaz

This is a skeleton flask application that can be launched on AWS Elastic Beanstalk. It is organized as follows:

- Install requirements (`requirements.txt`) in a virtual environment.
- See `flask_app/home/home.py` for main file.
- See `flask_app/utils/graph` and `flask_app/utils/database` for the BRAINWORKS database tools.
- See `flask_app/models.py` for the user database schema structure.

### Testing:

In development, this Flask app will default to the following:

- hosted on `localhost:5000`
- uses the config specified in `"config.DevConfig"` which:
  - Connects to the **live** graph API
  - Uses a **local user database** (requires no external configuration as it uses a bare-bones sqlite file)
  - runs in **DEBUG** mode
  - sets **ENV** to "development"

You have two options for running Flask:

1. Using my python script: `python3 run_dev.py`
   - use `--port` to specify a different port
   - use `--config` to specify a different config object
2. Using the Flask CLI: `flask run`
   - Must use a local `.flaskenv` in the root directory
   - To use a different port or config, specify them in `.flaskenv`. Example below.

#### Custom config

With either method, you may use a different config object.\
For example, I like to test locally with a MySQL database server and a local copy of the graph API, so I have a config file in `local/config.py` (gitignored) that looks like this:

```
from config import DevConfig

class LocalDevConfig(DevConfig):  # subclass the default DevConfig
    # locally hosted graph API
    GRAPH_API_URL = "localhost:5000"

    # locally hosted MySQL database
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://root:password@localhost:3306/localdb"
```

To run the flask app with this config, I can use `python3 run_dev.py --config local.config.LocalDevConfig`

#### Using a `.flaskenv`

Or, if I don't want to specify configs every time, I can instead use `flask run` with the following `.flaskenv` file in the root directory:

```
FLASK_ENV=development
FLASK_HOST=localhost
FLASK_RUN_PORT=5001
FLASK_APP=flask_app:create_app("path.to.local.config.LocalConfigObject")
```

\*Note that `FLASK_ENV`, `FLASK_HOST`, and `FLASK_RUN_PORT` are needed when using the Flask CLI because Flask hates configuration consistency, apparently.

### Database Migration

This app uses [Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/#command-reference) (which wraps around [Alembic](https://alembic.sqlalchemy.org/en/latest/)) to help facilitate database migration.

Be especially careful if you changed a table or column name, as Alembic cannot detect that and will generate a script which drops the table/column and creates a new one, which is BAD. You will need to manually rewrite those migration scripts by hand to alter the table/column instead.

Never commit a migration script that you haven't personally seen.

Here's what the typical workflow looks like:

1. Run the flask app
2. Make a change to the database model in the code (in `flask_app/auth/models.py`)
3. Run `flask db migrate` to automatically detect schema changes.\
   \*if your local database is out of date, run `flask db upgrade` first
4. **MANUALLY VERIFY** the generated migration script in `migrations/versions/`, rewrite it if necessary.
5. Run `flask db upgrade` to upgrade the local database
6. Then, when you push to production, run `flask db upgrade` to migrate the production database using that same script. This is why it must be manually verified.

If there is a conflict in the migration tree (maybe two people pushed different migrations to the database), they will need to be manually resolved using the `flask db merge`.
