from flask import (
    Blueprint,
    session,
    request,
    jsonify,
)
from flask import current_app as app, request
from flask_login import login_required
import json
import functools

from ..utils.utils import get_current_query
from ..utils.errors.errors import log_msg
from flask_app.models import Searches

# if in redshift environment, use the redshift queries
if app.config.get("DATA_DATABASE") == "REDSHIFT":
    from ..utils.graph import redshift_get_graph as get_graph
else:  # otherwise use the MySQL queries
    from ..utils.graph import get_graph

from ..admin.utils.searches import searches_charts

# Blueprint Configuration
home = Blueprint(
    "home",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/home",
)


def validate_csrf_post(f):
    """
    Route decorator to check if incoming post request has X-CSRFToken and matches it to the current session
    """

    @functools.wraps(f)
    def decorated_function(*args, **kws):
        if request.method == "POST":
            session_csrf = session.get("csrf_token")
            header_csrf = request.headers.get("x-csrftoken")
            if not session or not header_csrf or session_csrf != header_csrf:
                log_msg(
                    request.url,
                    f"Missing correct CSRF token. Session CSRF {session_csrf}  Header CSRF: {header_csrf}",
                )
                return jsonify(error="Missing correct CSRF token")
        return f(*args, **kws)

    return decorated_function


@app.route("/api/test", methods=["GET"])
def api_test():
    """
    Route for testing
    """
    pairs = get_graph.get_topic_citation_interest_query(
        {"include_mesh_concepts": ["lung", "covid"]}
    )
    return jsonify(success=pairs)


@app.route("/api/resume_session", methods=["GET"])
def api_resume_session():
    """
    Route to simply ping session to restart after user activity, so session doesn't expire
    """
    return jsonify(success="Session resumed")


@app.route("/api/visualizer-editor", methods=["GET"])
@validate_csrf_post
@login_required
def visualizer_editor():
    """
    Generates tool data based on current query in session
    """
    try:
        Searches.add_search(get_current_query())
        query = get_current_query()

        # Generate the graph. Will log errors if any occur
        rep = query.get("representation")  # Get tool representation
        if rep == "triples":
            graph_json_data, zip_data = get_graph.get_triples_data(query)
        elif rep == "paper_citations":
            graph_json_data, zip_data = get_graph.get_paper_citation_data(query)
        elif rep == "paper_triples":  # all triples for a single paper
            data, triples, zip_data = get_graph.get_single_paper_triples(query)
            if not triples:
                return jsonify(error="Couldn't get triples for this paper")
            return jsonify(
                success={
                    "representation": rep,
                    "data": {"paper": data, "triples": triples},
                    "zip_data": zip_data,
                }
            )
        elif rep == "topic_co_occurrences":
            graph_json_data, zip_data = get_graph.get_topic_co_occurrences(query)
        elif rep == "concept_embedding":
            graph_json_data, zip_data = get_graph.concept_embedding(query)
        else:  # default to knowledge map
            graph_json_data, zip_data = get_graph.get_triples_data(query)
        return jsonify(
            success={
                "representation": rep,
                "data": graph_json_data,
                "zip_data": zip_data,
            }
        )
    except Exception as e:
        log_msg(request.url, str(e), e)
        return jsonify(error=str(e))


@app.route("/api/autocomplete/<file>", methods=["GET"])
def autocomplete(file):
    """Serve the autocomplete files"""
    try:
        with open(f"flask_app/home/static/autocomplete/{file}.json") as f:
            response = jsonify(json.load(f))
        response.cache_control.max_age = 86400  # 1 day cache
        return response
    except Exception as e:
        log_msg(
            request.url,
            f"Autocomplete file '{file}' unavailable. {e.__class__.__name__}: {e}",
        )
        return jsonify(error="Can't get file")


# TODO: Extra functionality for visuals

# @home.route("/quick_search_papers_by_mesh_topic", methods=["GET"])
# # @login_required
# def quick_paper_topics():
#     """Return the top 10 papers with the given topics"""
#     # TODO Change to pulling from a static file that is updated weekly, just like the autocomplete.
#     topics = request.args.getlist("topics")
#     results = getGraph.search_paper_by_topic(topics, 10)
#     response = jsonify(results)
#     response.cache_control.max_age = 86400
#     return response


@home.route("/graph/command/<command>")
# @login_required
def graph_commands(command):
    """Received commands issued by the graph page"""
    args = request.args
    if command == "extra_topic_co_occurrences":
        result = get_graph.get_extra_topic_co_occurrences(
            args["topic"], int(args["start"]), int(args["num"]), session
        )
    else:
        return

    return jsonify(result)


# @home.route("/paper-info")
# # @login_required
# def paper_info():
#     """
#     Serve the Paper Info template.
#     Note that this is not the webpage, but the inner content of the paper info page.
#     This is used to display the paper info content inside iframes on other pages.
#     """
#     pmid = request.args.get("pmid")
#     if not pmid:
#         return error("PMID must be provided")

#     query = {"pmid": pmid}
#     data, triples, zip_data = getGraph.get_single_paper_triples(query)
#     return render_template(
#         "home/paper_triples.html", data=data, triples=triples, zip=zip_data
#     )
