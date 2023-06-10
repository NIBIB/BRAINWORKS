from flask import Flask, send_from_directory, send_file, render_template, render_template_string, request, make_response, redirect, jsonify
from flask_cors import cross_origin

import json
import os
import logging
from markdown import markdown



def create_app(config=None):
    """ Application factory to create the app and be passed to workers """
    app = Flask(__name__)

    if config:  # if given, use the specified configuration import path
        app.config.from_object(config)
        print(f"Using config: {config}")
    else:  # default to production configuration if none specified
        app.config.from_object('config.config.ProdConfig')

    # Setup logging
    logging.getLogger("werkzeug").level = logging.ERROR  # disable INFO logs for every resource request
    logging.basicConfig(
        filename='./logs/flask.log',
        level=logging.INFO,
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    @app.route("/ping", methods=['GET'])
    def ping():
        return "pong"

    @app.route('/', methods=['GET', 'POST'])
    @app.route('/index', methods=['GET', 'POST'])
    def index():
        return redirect("/documentation/latest")

    @app.route('/documentation')
    @app.route('/documentation/<string:version>', methods=['GET'])
    def documentation(version=None):
        """ Displays the full documentation """
        if not version or version == "latest" or not os.path.exists(f"app/versions/{version}"):
            version = app.config['VERSION']  # default to latest version

        with open(f"app/versions/{version}/html/documentation.md", "r") as file:
            html = markdown(file.read())  # convert to HTML
            html = render_template_string(html, domain=app.config["DOMAIN"])  # add jinja variables

        versions = os.listdir("app/versions")
        return render_template('documentation.html', html=html, versions=versions, version=version)

    @app.route('/documentation/example/<file>', methods=['GET'])
    def examples(file):
        """ Returns example JSON templates """
        if file not in ['graph_blank_template.json', 'graph_full_example.json', 'graph_mapping_example.json']:
            return "", 404
        with open(f'./documentation/{file}', 'r') as json_file:
            data = json.load(json_file)
            return data

    @app.route('/create_graph', methods=['GET', 'POST'])
    def create_graph(data=None):
        """ receive graph JSON from external source """
        if not data:  # if not passed into the function, take from request body
            if request.json:  # found in request body instead
                data = request.json
            else:
                logging.info("Graph data not found in /create_graph request")
                return "No graph data to process", 400
        logging.info("Received create_graph request")

        if app.config["ENV"] == "development":
            version = "local"
        else:
            version = "latest"

        return render_template("/graph.html", url=app.config["DOMAIN"], version=version, data=data)

    @app.route('/demo', methods=['GET'])
    def demo():
        """
        Return a demo graph page.
        This is meant to be navigated to in a browser, not for an API.
        """
        with open('app/static/demo_data.json') as file:
            data = json.load(file)

        if app.config["ENV"] == "development":
            version = "local"
        else:
            version = "latest"

        return render_template("/demo.html", url=app.config["DOMAIN"], version=version, data=data, debug=app.config["DEBUG"])

    @app.route('/build/<string:version>/<path:path>', methods=['GET'])
    @cross_origin()
    def versions(version, path):
        """ Serves fully built versions of the graph api and assets """
        if version == "latest" or not os.path.exists(f"app/versions/{version}"):
            version = app.config['VERSION']  # default to latest version

        # Render html templates from the versions directory
        if path.endswith(".html"):
            with open(f"app/versions/{version}/{path}") as file:
                return render_template_string(file.read(), domain=app.config["DOMAIN"])

        return send_from_directory(f"versions/{version}", path)

    @app.errorhandler(404)
    def page_not_found(error):
        return 'This route does not exist: {}'.format(request.url), 404

    @app.errorhandler(500)
    def internal_error(error):
        logging.error(f"{error}")
        return "500 error (caught by error handler)"

    return app
