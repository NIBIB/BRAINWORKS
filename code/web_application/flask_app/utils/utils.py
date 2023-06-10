from flask import session

def get_current_query():
    """ Gets the query last run from the session """
    queries = session.get('queries', {})
    if not queries:
        return {}
    rep = queries.get('representation')
    if not rep:
        return {}
    query = queries.get(rep, {})
    return query

def set_current_query(query):
    """ Set the current query """
    rep = query.get('representation')
    if not rep:
        raise Exception("Could not set query. Query did not provide a representation")
    queries = session.get('queries', {})
    queries["representation"] = rep
    queries[rep] = query  # set query for this representation

    session['queries'] = queries
    session.modified = True