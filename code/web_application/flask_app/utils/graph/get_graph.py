from ..database.database import database

import mysql.connector
import logging
from collections import Counter
from datetime import datetime
import os

import pandas as pd
import numpy as np
import json
from io import BytesIO
import zipfile
from base64 import b64encode


db = database()


def execute(query, params=[], raise_no_results=True, show_query=False):
    """execute the given query"""
    if show_query:
        logging.info(query)
        logging.info("Params: ", params)

    try:
        result = db.query(query, parameters=params)
    except mysql.connector.errors.ProgrammingError as e:
        logging.exception(e)
        raise Exception("Critical error in database query. This error has been logged.")
    except mysql.connector.errors.DatabaseError as e:
        logging.exception(e)
        raise Exception(
            "Unable to connect to the database. This likely means that the database is temporarily unavailable - please try again later."
        )
    except Exception as e:
        logging.exception(e)
        raise Exception("Uncaught Database Error.")

    if raise_no_results and len(result) == 0:
        raise Exception(
            "Your query returned no results. Try reducing the specificity of your search"
        )
    return result


def create_zip(dataframe, name="data"):
    """
    Given a pandas dataframe and file name, create a base-64 encoded zip file with the contents in CSV format.
    <dataframe> can instead be a list of tuples for multiple dataframes:
        [(df1, name1), (df2, name2), ...]
    """
    if (
        type(dataframe) != list
    ):  # if dataframe isn't a list, convert it to a list of the tuple
        dataframe = [(dataframe, name)]

    zip_buffer = BytesIO()  # zip file buffer

    # create csv files
    for (df, filename) in dataframe:
        csv_buf = BytesIO()
        csv_buf.seek(0)
        df.to_csv(csv_buf, encoding="utf-8-sig")  # utf-8 with BOM

        # write csv contents
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            zip_file.writestr(f"{filename}.csv", csv_buf.getvalue())  # write csv

    b = zip_buffer.getvalue()
    encoded = b64encode(b).decode("utf-8")
    return encoded


def highlight_abstract(text, triples):
    """
    Given an abstract and a dictionary of triples (with start_char and end_char),
    add HTML tags around the corresponding sections of text.
    """
    i = 0
    highlighted = ""
    prev_end = 0
    for triple in triples:
        start = triple.get("start_char")
        end = triple.get("end_char") + 1
        if start is None or end is None:
            continue
        section = f"{text[prev_end:start]}<span class='highlight' data-index='{i}'>{text[start:end]}</span>"
        highlighted += section
        i += 1
        prev_end = end
    highlighted += text[prev_end:]
    return highlighted


def abstract_into_list(text, triples):
    """
    Given an abstract and a dictionary of triples (with start_char and end_char),
    break abstract into nested string list, with 2nd value indicating if it is associated with a triple,
    ex: [['text']['text', '1']]
    """
    i = 0
    abstract_list = []
    prev_end = 0
    for triple in triples:
        start = triple.get("start_char")
        end = triple.get("end_char") + 1
        if start is None or end is None:
            continue
        abstract_list.append([text[prev_end:start]])
        abstract_list.append([text[start:end], i])
        i += 1
        prev_end = end
    abstract_list.append([text[prev_end:]])
    return abstract_list


########
# Partial SQL query components
########


def filter_affiliations(params, data):
    """Create a WHERE clause to filter by paper affiliations"""
    if params.get("authors"):
        # format string for the CASE statements for names
        statements = []
        for author in params["authors"]:
            author = author.split(" ")  # split name by spaces
            if len(author) == 1:  # only 1 name given, assume last name
                statement, author_data = filter_by_author(last_name=author[0])
            else:  # else, assume first and last. Ignore middle names for now.
                statement, author_data = filter_by_author(
                    first_name=author[0], last_name=author[-1]
                )
            statements.append(statement)
            data += author_data
        return "AND " + " OR ".join(statements)
    else:
        return ""


def filter_by_author(first_name=None, last_name=None, match_exact=False):
    """
    Create the inner part of a WHERE statement to filter the affiliation table by author name.
    By default, a search for "J D" will match "John Doe", and vise versa, unless <match_exact> is True.
    """
    first, last = "", ""
    params = []

    # match names exactly
    if match_exact:
        if first_name:
            first = "first_name LIKE %s"
            params.append(first_name)
        if last_name:
            last = f"last_name LIKE %s"
            params.append(last_name)

    # TODO also match names where the database has multiple last names or multiple first names
    else:  # match initials and similar names too
        if first_name:
            if len(first_name) == 1:  # first initial supplied - match all possibilities
                first = f"first_name LIKE %s"
                params.append(f"{first_name}%")
            else:  # full first name supplied, match only the first initial too
                first = f"(first_name LIKE %s OR first_name LIKE %s)"
                params += [first_name, first_name[0]]

        if last_name:
            if len(last_name) == 1:  # last initial supplied - match all possibilities
                last = f"last_name LIKE %s"
                params.append(f"{last_name}%")
            else:  # full last name supplied, match only the last initial too
                last = f"(last_name LIKE %s OR last_name LIKE %s)"
                params += [last_name, last_name[0]]

    if first_name and last_name:
        statement = f"({first} AND {last})"
    else:
        statement = first + last
    return statement, params


def filter_include_concepts(params, data, column):
    """create the WHERE clause to filter a SQL query by object and subject search terms"""
    terms = ""
    if params.get("include_concepts"):
        terms += (
            f"AND {column} IN ({','.join('%s' for _ in params['include_concepts'])})"
        )
        data += params["include_concepts"]
    return terms


def filter_exclude_concepts(params, data, column):
    terms = ""
    if params.get("exclude_concepts"):
        terms += (
            f" AND {column} IN ({','.join('%s' for _ in params['exclude_concepts'])})"
        )
        data += params["exclude_concepts"]
    return terms


def filter_relations(params, data, column):
    """create the WHERE clause to filter a SQL query by relation search terms"""
    terms = ""
    if params.get("include_relations"):
        terms += (
            f"AND {column} IN ({','.join('%s' for _ in params['include_relations'])})"
        )
        data += params["include_relations"]

    if params.get("exclude_relations"):
        terms += f" AND {column} NOT IN ({','.join('%s' for _ in params['exclude_relations'])})"
        data += params["exclude_relations"]

    return terms


def filter_projects(params, data):
    """Create a WHERE statement o filter by the projects table"""
    if params.get("grants"):
        statements = []
        for number in params["grants"]:
            statements.append(f"core_project_num = %s")
            data.append(number)
        return f"""AND ({"OR ".join(statements)})"""
    else:
        return ""


def filter_publications(params, data):
    """Create a WHERE statement o filter by the publications table"""
    if params.get("journals"):
        statements = []
        for title in params["journals"]:
            statements.append(f"journal_title LIKE %s")
            data.append(f"%{title}%")
        return "AND " + " OR ".join(statements)
    else:
        return ""


def limit(params, data, default=1000):
    """Create a LIMIT statement"""
    data.append(params.get("limit", default))
    return f"LIMIT %s"


# Paper Citation Map
def paper_citations_query(params):
    """construct and execute a SQL query for an author citation graph"""
    data = []  # SQL query parameters

    query = "WITH RECURSIVE"

    query += f"""
    filtered_papers AS (
        SELECT t.pmid
        FROM triples_filtered_relations_concepts t
        WHERE concept_type IN ('subject', 'object')
        {filter_include_concepts(params, data, 'concept_name')}
        GROUP BY t.pmid
    )
    
    -- track the "parent" of each citation chain here
    , filtered_citations AS (
        SELECT c.pmid, c.citedby, c.citation_date, ROW_NUMBER() OVER(ORDER BY p.pmid) as parent_id
        FROM filtered_papers p
        JOIN citation_graph_filtered_relations c ON p.pmid = c.pmid
    )
    
    , l1 AS (
        SELECT f.pmid, f.citedby, f.citation_date, parent_id, 0 as depth
            FROM filtered_citations f
        UNION ALL
        SELECT c.pmid, c.citedby, c.citation_date, parent_id, 1 as depth
            FROM filtered_citations f
            JOIN citation_graph_filtered_relations c ON f.citedby = c.pmid
    )
    
    , l2 AS (
        SELECT f.pmid, f.citedby, f.citation_date, parent_id, depth
            FROM l1 f
        UNION ALL
        SELECT c.pmid, c.citedby, c.citation_date, parent_id, 2 as depth
            FROM l1 f
            JOIN citation_graph_filtered_relations c ON f.citedby = c.pmid
    )
    
    , unique_citations AS (
        SELECT 
            pmid, citedby, parent_id,
            MIN(depth) as depth
        FROM l2
        GROUP BY pmid, citedby, parent_id
    )
    
    , parent_size AS (
       SELECT parent_id, COUNT(parent_id) num
       FROM unique_citations
       GROUP BY parent_id
       ORDER BY num DESC
    )
    
    , results AS (
        SELECT c.* FROM unique_citations c
        JOIN parent_size p ON p.parent_id = c.parent_id
        ORDER BY c.parent_id, depth
        {limit(params, data, 500)}
    )
        
    SELECT * FROM results;
    """

    citations = execute(query, data)
    pmids = set()
    for c in citations:
        pmids.add(c['pmid'])
        pmids.add(c['citedby'])

    # get paper data for all pmids from the previous query
    info_query = f"""
        SELECT *
        FROM paper_info_filtered_relations
        WHERE pmid IN ({','.join(['%s' for _ in pmids])})
    """
    paper_info = execute(info_query, list(pmids))

    return citations, paper_info


def get_paper_citation_data(params):
    """
    Get all data for the Paper Citation graph.
    Create the JSON data for the Graph API and the Base64 encoded ZIP data to export.
    """
    citations, paper_info = paper_citations_query(params)
    df = pd.DataFrame(citations)

    # create base-64 encoded zip file
    zip_data = create_zip([(df, 'citations'), (pd.DataFrame(paper_info), "papers")])

    # turn paper info into dict for easy lookup
    papers = {}
    for row in paper_info:
        papers[row['pmid']] = row

    # turn citations into dict if a list of pmids that cited it for easy lookup
    citation_dict = {}
    max_depth = 0  # track maximum depth
    for row in citations:
        pmid = row['pmid']
        citedby = row['citedby']
        depth = row['depth']
        if not citation_dict.get(pmid):  # if target pmid not in dict, add it
            citation_dict[pmid] = []
        if not citation_dict.get(citedby):  # if source pmid not in dict, add it too
            citation_dict[citedby] = []
        citation_dict[pmid].append(citedby)  # append this citation to the dict
        papers[pmid]['depth'] = depth  # add depth to paper info dict
        if depth > max_depth:
            max_depth = depth

    nodes, edges = [], []
    added_nodes = set()  # keep track of nodes added
    for i, target_pmid in enumerate(citation_dict.keys()):  # iterate through all citations
        sources = citation_dict[target_pmid]
        info = papers.get(target_pmid,{})

        doi = ""
        if info.get("doi"):
            doi = "https://doi.org/" + info["doi"]

        title = info.get("pub_title") or "title unavailable"
        depth = info.get("depth", max_depth)

        pub_date = info.get("pub_date")
        if pub_date:
            pub_date = datetime(year=pub_date.year, month=pub_date.month, day=pub_date.day).timestamp()

        authors = ""
        if info.get("authors"):
            authors = (", ").join(info["authors"].split(";"))

        if target_pmid not in added_nodes:  # new node
            added_nodes.add(target_pmid)
            nodes.append(
                {
                    "key": target_pmid,
                    "attributes": {
                        "label": title,
                        "data": {
                            "pmid": target_pmid,
                            "time": pub_date,
                            "doi": doi,
                            "title": info.get("pub_title"),
                            "authors": authors,
                            "abstract": info.get("abstract"),
                            "journal_title": info.get("journal_title"),
                            "depth": str(depth),
                        },
                    },
                }
            )

        # add an edge if both papers present with citation date, and it doesn't cite itself.
        for j, source_pmid in enumerate(sources):  # for each source pmid
            if target_pmid == source_pmid:  # self-citation
                continue
            edges.append(
                {
                    "key": f"{i}_{j}",
                    "source": source_pmid,
                    "target": target_pmid,
                    "attributes": {
                        "label": "cited",
                        "type": "arrow",
                        "data": {},
                    },
                }
            )

    config = {
        "maps": {
            "node_size": {"data": "degree", "min": 10, "max": 30},
            "node_color": {
                "data": "depth",
                "map": {"0": "#FF0000", "1": "#F9BC06", "2": "#DCA14D", "3": "#D4C291"},
            },
        },
        "filters": {  # sliders
            # "Node Time": {"type": "node", "data": "time", "format": "date"},
            # "Edge Time": {"type": "edge", "data": "time", "format": "date"}
        },
        "settings": {},
    }

    graph = {"nodes": nodes, "edges": edges}
    json_data = {"graph": graph, "config": config}
    return json_data, zip_data


# Knowledge Map
def triples_query(params):
    """Construct and execute a SQL query for the knowledge graph from the given parameters"""
    data = []  # SQL query parameters

    if_exclude_concepts = params.get("exclude_concepts")
    if_include_concepts = params.get("include_concepts")

    # for the definitions (because they get real long)
    query = "SET SESSION group_concat_max_len = 4096;"
    execute(query, raise_no_results=False)

    # main query
    query = "WITH "

    if if_exclude_concepts:
        query += f"""
        excluded_concepts AS (
            SELECT pmid, triple_id
            FROM triples_filtered_relations_concepts c
            WHERE concept_type IN ("subject", "object")
            {filter_exclude_concepts(params, data, 'concept_name')}
        ),
        """

    if if_include_concepts:
        query += f"""
        included_concepts AS (
            SELECT pmid, triple_id
            FROM triples_filtered_relations_concepts c
            WHERE concept_type IN ("subject", "object")
            {filter_include_concepts(params, data, 'concept_name')}
        )
        """

    where = False
    query += f"""
        SELECT * 
        FROM triple_graph_filtered_relations t
    """
    if if_include_concepts:
        query += "WHERE (t.pmid, t.triple_id) IN (SELECT * FROM included_concepts)"
        where = True
    if if_exclude_concepts:
        query += f"{' AND' if where else 'WHERE'} (t.pmid, t.triple_id) NOT IN (SELECT * FROM excluded_concepts)"
    query += f"""
    {limit(params, data, 1000)}
    """

    triples = execute(query, data)

    # all UNIQUE concept IDs in the triples returned
    all_concept_ids = list(
        set(
            [id for t in triples for id in t["subject_umls_topics"].split(";")]
            + [id for t in triples for id in t["object_umls_topics"].split(";")]
            + [id for t in triples for id in t["relation_umls_topics"].split(";")]
        )
    )
    placeholders = ",".join(["%s" for _ in all_concept_ids])
    params = all_concept_ids * 2
    concept_query = f"""
    WITH 
    
    concepts AS (
        SELECT * FROM triples_filtered_relations_concepts c
        WHERE c.concept_id IN ({placeholders})
        GROUP BY c.concept_id
    )
    
    , defs AS (
        SELECT CUI, MAX(DEF) as DEF FROM definitions_filtered_relations d
        WHERE CUI IN ({placeholders})
        AND d.DEF is not NULL
        GROUP BY CUI
    )
    
    SELECT c.concept_id as CUI, c.concept_name as name, d.DEF as definition
    FROM concepts c
    LEFT JOIN defs d ON c.concept_id = d.CUI
    """
    concepts = execute(concept_query, params)

    return triples, concepts


def get_triples_data(params):
    """
    Get all data for the Knowledge Map graph.
    Create the JSON data for the Graph API and the Base64 encoded ZIP data to export.
    """
    triples, concepts = triples_query(params)
    df = pd.DataFrame(triples)
    zip_data = create_zip(df)  # create base-64 encoded zip file

    # construct dictionary for concept CUIs
    concepts = {c["CUI"]: c for c in concepts}

    # dropping object
    df1 = df.drop(columns=["object", "object_umls_topics"])

    # dropping subject and renaming object to subject
    df2 = df.drop(columns=["subject", "subject_umls_topics"]).rename(
        columns={"object": "subject", "object_umls_topics": "subject_umls_topics"}
    )

    # union of dataframes (all subject/object are not just subject)
    df3 = pd.concat([df1, df2])
    df3.reset_index(inplace=True)

    # getting the earliest data appearance of subject and converting to dict
    min_dates = {}
    for i, row in df3.iterrows():
        lowest = min_dates.get(row["subject"])
        cur = row["pub_date"]
        if lowest is not None and cur is not None:
            if cur < lowest:  # this date is lower
                min_dates[row["subject"]] = cur  # new lowest
        else:  # no date here yet
            min_dates[row["subject"]] = cur

    # This gets the names of every node
    raw_nodes = dict(
        Counter(
            [triple["subject"] for triple in triples]
            + [triple["object"] for triple in triples]
        )
    )
    nodes, edges = [], []

    node_map = {}  # map of nodes and their list of concept CUIs
    topic_map = {}  # map of topics and their frequencies
    for node, cnt in raw_nodes.items():
        ind = df3.subject.isin([node])
        ii = df3[ind].index.values[0]
        topic_ids = df3.iloc[ii]["subject_umls_topics"].split(
            ";"
        )  # if ii is not 0 else None
        node_map[node] = topic_ids
        for id in topic_ids:
            topic_map[id] = topic_map.get(id, 0) + 1  # increment topic count

    # now loop through again and assign node data
    for node, cnt in raw_nodes.items():
        # date
        dt = min_dates[node]
        timestamp = datetime(year=dt.year, month=dt.month, day=dt.day).timestamp()
        node_data = {"time": timestamp}

        # topics
        node_map[node].sort(
            reverse=True, key=lambda id: topic_map[id]
        )  # sort node topics by frequency
        node_concepts = []  # list of concepts for this node
        for i, id in enumerate(node_map[node]):  # assign node data in that order
            concept = concepts.get(id)  # get the concept for this id
            name, definition = "", ""
            if concept:
                node_concepts.append(concept)
                name = concept["name"]
                definition = concept["definition"]
            node_data[f"topic-{i+1}"] = name
            node_data[f"definition-{i+1}"] = definition

        # average embedding information between all concepts

        node = {"key": node, "attributes": {"label": node, "data": node_data}}
        nodes.append(node)

    edge_map = (
        {}
    )  # map of source nodes and target nodes. Used to keep track of how many of each edge was added
    for i, triple in enumerate(triples):
        # creating the date object of today's date
        if triple["doi"]:
            doi = "https://doi.org/" + triple["doi"]
        else:
            doi = ""

        pub_date = triple["pub_date"]
        timestamp = datetime(
            year=pub_date.year, month=pub_date.month, day=pub_date.day
        ).timestamp()

        source = triple["subject"]
        target = triple["object"]

        # This is just to restrain the edges to 1 edge per pair of nodes because sigma can't display multiple.
        if edge_map.get(source):
            if edge_map[source].get(target):  # this edge was already added
                continue
            else:
                edge_map[source][target] = True  # add this target to this source
        elif edge_map.get(target):
            if edge_map[target].get(source):
                continue
            else:
                edge_map[target][source] = True
        else:
            edge_map[source] = {target: True}  # add this source and target

        edges.append(
            {
                "key": str(i),
                "source": source,
                "target": target,
                "attributes": {
                    "label": triple["relation"],
                    "type": "arrow",
                    "data": {
                        "triple": f"{triple['subject']} {triple['relation']} {triple['object']}",
                        "pmid": triple["pmid"],
                        "citations": triple["citations"] or 0,
                        "time": timestamp,
                        "doi": doi,
                        "title": triple["pub_title"],
                        "authors": (", ").join(triple["authors"].split(";")),
                        "abstract": triple["abstract"],
                        "start_char": triple["start_char"],
                        "end_char": triple["end_char"],
                        "confidence": triple["confidence"],
                        "journal_title": triple["journal_title"],
                        "sentiment": str(
                            hardcoded_sentiment(
                                [
                                    concepts[id]["name"]
                                    for id in triple["relation_umls_topics"].split(";")
                                ]
                            )
                        ),
                    },
                },
            }
        )

    # the config dict to pass to the graph API
    config = {
        "maps": {
            "cluster": ["topic-1"],  # empty for automatic organizing
            "node_size": {"data": "degree", "min": 10, "max": 40},
            # "node_color": {"data": "topic-1"},
            "edge_size": {"data": "citations", "min": 5, "max": 10},
            "edge_color": {
                "data": "sentiment",
                "map": {"-1": "#ff4d4d", "0": "#585858", "1": "#3366ff"},
            },
            "cluster_edge_size": {"type": "avg"},
            # "node_x": {"data": "2a", "min": -10, "max": 10},
            # "node_y": {"data": "2b", "min": -10, "max": 10},
            # "node_color": {"data": ["3a", "3b", "3c"]},
            "node_color": {"data": "topic-1"},
        },
        "filters": {  # sliders
            "Node Time": {"type": "node", "data": "time", "format": "date"},
            "Edge Time": {"type": "edge", "data": "time", "format": "date"},
            "Paper Citations": {"type": "edge", "data": "citations"},
        },
        "settings": {"cluster_MISC": "hide", "cluster_level": 1},
    }

    graph = {"nodes": nodes, "edges": edges}
    json_data = {"graph": graph, "config": config}

    return json_data, zip_data


def hardcoded_sentiment(relations):
    """
    returns a sentiment score that I manually hardcoded based on the relation
    """
    min_score, max_score = -1, 1
    score = 0
    for relation in relations:
        if relation in [
            "Increased",
            "Increase",
            "Increasing",
            "Improved",
            "Improved",
            "Positive",
            "Enhance (action)",
            "Promotion (action)",
            "Induce (action)",
        ]:
            score += 1
        elif relation in [
            "Decrease",
            "Decreased",
            "Reduced",
            "Suppressed",
            "Inhibited",
            "Negative",
        ]:
            score -= 1
    score = max(min_score, score)
    score = min(max_score, score)
    return score


# Concept embedding
def concept_embedding(params):
    query = """
    SELECT
        c.CUI, c.AUI, c.STR,
        e.2a, e.2b,
        e.3a, e.3b, e.3c,
        e.5a, e.5b, e.5c, e.5d, e.5e
    FROM concept_embeddings e
    JOIN concept_map c ON c.CUI = e.CUI AND c.AUI = e.AUI
    LIMIT %s
    """
    data = [params.get("limit", 1000)]
    rows = execute(query, data)

    df = pd.DataFrame(rows)
    zip_data = create_zip(df)  # create base-64 encoded zip file

    nodes, edges = [], []

    # now loop through again and assign node data
    for row in rows:
        node = {
            "key": row["AUI"],
            "attributes": {
                "label": row["STR"],
                "data": {
                    "2a": row["2a"],
                    "2b": row["2b"],
                    "3a": row["3a"],
                    "3b": row["3b"],
                    "3c": row["3c"],
                    "5a": row["5a"],
                    "5b": row["5b"],
                    "5c": row["5c"],
                    "5d": row["5d"],
                    "5e": row["5e"],
                },
            },
        }
        nodes.append(node)

    # the config dict to pass to the graph API
    config = {
        "maps": {
            "node_x": {"data": "5a", "min": -10, "max": 10},
            "node_y": {"data": "5b", "min": -10, "max": 10},
            "node_color": {"data": ["5a", "5b", "5c"]},
        },
        "filters": {},  # sliders
        "settings": {"toolbar": ["menu", "center", "search", "controls"]},
    }

    graph = {"nodes": nodes, "edges": edges}
    json_data = {"graph": graph, "config": config}

    return json_data, zip_data


# Single paper triples data
def get_single_paper_triples(params):
    """Construct and execute a SQL query for the knowledge graph from the given parameters"""
    pmid = params.get("pmid")
    pub_query = f"""
    SELECT * FROM paper_info_filtered_relations
    WHERE pmid = %s
    LIMIT 1
    """
    data = execute(pub_query, [pmid])[0]
    data = {
        "pmid": data["pmid"],
        "pub_title": data["pub_title"] or "[title unavailable]",
        "doi": "https://doi.org/" + data["doi"] if data["doi"] else "",
        "authors": (", ").join(data["authors"].split(";"))
        if data["authors"]
        else "[authors unavailable]",
        "pub_date": data["pub_date"],
        "abstract": data["abstract"] or "",
    }

    # triples
    triple_query = f"""
    WITH
    # This makes sure the unique concepts are pulled.
    # technically they should already be unique in the database, but this is just in case
    concepts AS (
        SELECT * FROM triples_filtered_relations_concepts c
        WHERE pmid = %s
        GROUP BY c.triple_id, c.concept_type, c.concept_id, c.start_char, c.end_char, c.frag_start_char, c.frag_end_char
    )
    
    SELECT 
        t.subject,
        t.relation,
        t.object,
        t.start_char,
        t.end_char,
        GROUP_CONCAT(DISTINCT cs.id SEPARATOR ';') as subject_umls_topics,
        GROUP_CONCAT(DISTINCT co.id SEPARATOR ';') as object_umls_topics
    FROM triple_graph_filtered_relations t
    LEFT JOIN concepts cs ON cs.pmid = t.pmid AND cs.triple_id = t.triple_id AND cs.concept_type = 'subject' AND cs.concept_name IS NOT NULL
    LEFT JOIN concepts co ON co.pmid = t.pmid AND co.triple_id = t.triple_id AND co.concept_type = 'object'  AND co.concept_name IS NOT NULL
    WHERE t.pmid = %s
    GROUP BY subject, object
    ORDER BY (cs.total_concepts + co.total_concepts) DESC
"""
    triples = execute(triple_query, [pmid, pmid])
    df = pd.DataFrame(triples)
    zip_data = create_zip(df)  # create base-64 encoded zip file

    all_concept_ids = []
    for t in triples:
        if t["subject_umls_topics"]:
            all_concept_ids.extend([id for t in triples for id in t["subject_umls_topics"].split(";")])
        if t["object_umls_topics"]:
            all_concept_ids.extend([id for t in triples for id in t["object_umls_topics"].split(";")])

    concepts = {}
    if len(all_concept_ids):  # if any concepts found for this paper
        concept_query = f"""
            SELECT c.*, d.DEF as definition
            FROM triples_filtered_relations_concepts c
            LEFT JOIN definitions_filtered_relations d ON c.concept_id = d.CUI
            WHERE c.id IN ({','.join(['%s' for _ in all_concept_ids])})
            AND c.pmid = %s
            GROUP BY c.id, d.CUI
        """
        concepts = execute(concept_query, all_concept_ids+[pmid], raise_no_results=False)
        concepts = {int(c["id"]): c for c in concepts}

    # highlight text
    # data['abstract'] = highlight_abstract(data['abstract'], triples)
    data["abstract"] = abstract_into_list(data["abstract"], triples)

    # parse triple information
    for triple in triples:

        triple["subject_topics"] = []
        if triple["subject_umls_topics"]:
            triple["subject_topics"] = [concepts.get(int(id)) for id in triple["subject_umls_topics"].split(";")]
        triple["object_topics"] = []
        if triple["object_umls_topics"]:
            triple["object_topics"] = [concepts.get(int(id)) for id in triple["object_umls_topics"].split(";")]

    return data, triples, zip_data


# Topic co-occurrences
def topic_co_occurrences_query(params):
    include_mesh_concepts = params.get("include_mesh_concepts")
    exclude_mesh_concepts = params.get("exclude_mesh_concepts")
    limit = params.get("limit")
    data = []  # injected parameters for the query

    # SQL query WHERE statements
    include_topics_where = ""
    exclude_topics_where = ""
    if include_mesh_concepts:
        s = ", ".join("%s" for _ in include_mesh_concepts)  # placeholders
        include_topics_where = f"WHERE (topic_1 IN ({s}) OR topic_2 IN ({s}))"
        data += include_mesh_concepts  # twice because the list is in the query twice
        data += include_mesh_concepts
    if exclude_mesh_concepts:
        s = ", ".join("%s" for _ in exclude_mesh_concepts)  # placeholders
        where = "AND" if include_mesh_concepts else "WHERE"  # WHERE or AND
        exclude_topics_where = (
            f"{where} (topic_1 NOT IN ({s}) AND topic_2 NOT IN ({s}))"
        )
        data += exclude_mesh_concepts  # twice because the list is in the query twice
        data += exclude_mesh_concepts

    if not limit:
        limit = 1000
    data.append(limit)

    query = f"""
    WITH results AS (
        SELECT 
            topic_1, topic_2,
            total_1, total_2,
            def_1, def_2,
            delta, frequency, relevance, avg_prob,
            ROW_NUMBER() OVER(PARTITION BY topic_1 ORDER BY ABS(delta) DESC) AS delta_order,
            ROW_NUMBER() OVER(PARTITION BY topic_1 ORDER BY frequency DESC) AS frequency_order
        FROM topic_co_occurrence_graph_filtered
        {include_topics_where}
        {exclude_topics_where}
    )
    SELECT * FROM results
    WHERE (delta_order = 1)
    ORDER BY relevance / 10000000*avg_prob DESC
    LIMIT %s
    """
    pairs = execute(query, data)
    return pairs


def get_topic_co_occurrences(params):
    # update_topic_co_occurrence_table()
    pairs = topic_co_occurrences_query(params)

    pairs_df = pd.DataFrame(pairs)
    zip_data = create_zip(pairs_df, "co-occurrences")  # create base-64 encoded zip file

    nodes, added_nodes = [], set()
    edges, edge_map = [], {}  # map of edges to keep track of duplicate combinations

    for row in pairs:
        topic_1 = row["topic_1"]
        topic_2 = row["topic_2"]
        delta_order = row["delta_order"]
        frequency_order = row["frequency_order"]

        # This populates the edge_map with the lowest value of delta_order and frequency_order,
        # ensuring that only one combination of topic_1 and topic_2 is in the map.

        if edge_map.get(topic_1):
            if edge_map[topic_1].get(topic_2):  # this edge was already added
                edge_map[topic_1][topic_2]["delta_order"] = min(
                    edge_map[topic_1][topic_2]["delta_order"], delta_order
                )  # set whichever order is lower
                edge_map[topic_1][topic_2]["frequency_order"] = min(
                    edge_map[topic_1][topic_2]["frequency_order"], frequency_order
                )
            else:
                edge_map[topic_1][topic_2] = {
                    "delta_order": delta_order,
                    "frequency_order": frequency_order,
                }
        elif edge_map.get(topic_2):
            if edge_map[topic_2].get(topic_1):
                edge_map[topic_2][topic_1]["delta_order"] = min(
                    edge_map[topic_2][topic_1]["delta_order"], delta_order
                )  # set whichever order is lower
                edge_map[topic_2][topic_1]["frequency_order"] = min(
                    edge_map[topic_2][topic_1]["frequency_order"], frequency_order
                )
            else:
                edge_map[topic_2][topic_1] = {
                    "delta_order": delta_order,
                    "frequency_order": frequency_order,
                }
        else:
            edge_map[topic_1] = {
                topic_2: {
                    "delta_order": delta_order,
                    "frequency_order": frequency_order,
                }
            }  # add this source and target

    for row in pairs:
        # some results need to be converted from the weird SQL decimal type to regular float
        topic_1 = row["topic_1"]
        topic_2 = row["topic_2"]
        def_1 = row.get("def_1")
        def_2 = row.get("def_2")
        total_1 = float(row["total_1"])  # current absolute total occurrences of topic_1
        total_2 = float(row["total_2"])  # current absolute total occurrences of topic_2

        delta = float(row["delta"])  # proportional change in frequency
        frequency = float(row["frequency"])  # current proportional frequency

        if edge_map.get(topic_1) and edge_map[topic_1].get(
            topic_2
        ):  # if the initial ordering is in the edge map
            t1, t2 = topic_1, topic_2
        elif edge_map.get(topic_2) and edge_map[topic_2].get(
            topic_1
        ):  # if the reverse order is in the edge map
            t1, t2 = topic_2, topic_1  # swap em
        else:  # if neither order is in the edge map, something went wrong when creating the edge map.
            logging.warning(
                "Something went wrong when creating the edge map for the topic co-occurrence graph. The combination of topics wasn't found in the edge map."
            )
            continue  # skip it
        delta_order = edge_map[t1][t2]["delta_order"]  # get lowest values
        frequency_order = edge_map[t1][t2]["frequency_order"]

        # add new edge
        edges.append(
            {
                "key": f"{topic_1}--{topic_2}",
                "source": topic_1,
                "target": topic_2,
                "attributes": {
                    "label": "",
                    "data": {
                        "delta": delta,
                        "delta_order": delta_order,
                        "frequency": frequency,
                        "frequency_order": frequency_order,
                    },
                },
            }
        )

        # add topic 1 if new
        if topic_1 not in added_nodes:
            nodes.append(
                {
                    "key": topic_1,
                    "attributes": {
                        "label": topic_1,
                        "color": "#000000",
                        "data": {"total": total_1, "definition": def_1},
                    },
                }
            )
            added_nodes.add(topic_1)

        # add topic 2 if new
        if topic_2 not in added_nodes:
            nodes.append(
                {
                    "key": topic_2,
                    "attributes": {
                        "label": topic_2,
                        "color": "#000000",
                        "data": {"total": total_2, "definition": def_2},
                    },
                }
            )
            added_nodes.add(topic_2)

    # the config dict to pass to the graph API
    config = {
        "maps": {
            "node_size": {"data": "total", "min": 5, "max": 30},
            "edge_size": {"data": "frequency", "min": 5, "max": 30},
            "edge_color": {
                "data": "delta",
                "map": {"mid": 0, "colors": ["#ff5050", "#cccccc", "#3366ff"]},
            },
        },
        "filters": {  # sliders
            # "Delta Order": {"type": "edge", "data": "delta_order"},
            "Total Topic Occurrences": {"type": "node", "data": "total"},
            "Co-Occurrence Frequency": {"type": "edge", "data": "frequency"},
        },
        "settings": {"edge_filters_hide_nodes": True},
    }

    graph = {"nodes": nodes, "edges": edges}
    json_data = {"graph": graph, "config": config}
    return json_data, zip_data


def get_extra_topic_co_occurrences(topic, start, num):
    """
    Get extra topics to add to the co-occurrence graph.
    <start> is the starting row to return
    <num> is the number of rows to return
    """
    query = f"""
    WITH results AS (
        SELECT 
            topic_1, topic_2,
            total_1, total_2,
            def_1, def_2,
            delta, frequency, relevance, avg_prob,
            ROW_NUMBER() OVER(PARTITION BY topic_1 ORDER BY ABS(delta) DESC) AS delta_order,
            ROW_NUMBER() OVER(PARTITION BY topic_1 ORDER BY frequency DESC) AS frequency_order
        FROM topic_co_occurrences
        WHERE topic_1 = %s
    )
    SELECT * FROM results
    ORDER BY delta_order ASC
    LIMIT %s, %s
    """
    data = [topic, start, num]
    pairs = execute(query, data, raise_no_results=False)

    nodes, added_nodes = [], set()
    edges, edge_map = [], {}  # map of edges to keep track of duplicate combinations

    for row in pairs:
        # some results need to be converted from the weird SQL decimal type to regular float
        topic_1 = row["topic_1"]
        topic_2 = row["topic_2"]
        def_1 = row.get("def_1")
        def_2 = row.get("def_2")
        total_1 = float(row["total_1"])  # current absolute total occurrences of topic_1
        total_2 = float(row["total_2"])  # current absolute total occurrences of topic_2

        delta = float(row["delta"])  # proportional change in frequency
        frequency = float(row["frequency"])  # current proportional frequency

        delta_order = row["delta_order"]  # get lowest values
        frequency_order = row["frequency_order"]

        # add new edge
        edges.append(
            {
                "key": f"{topic_1}--{topic_2}",
                "source": topic_1,
                "target": topic_2,
                "attributes": {
                    "label": "",
                    "data": {
                        "delta": delta,
                        "delta_order": delta_order,
                        "frequency": frequency,
                        "frequency_order": frequency_order,
                    },
                },
            }
        )

        # add topic
        nodes.append(
            {
                "key": topic_1,
                "attributes": {
                    "label": topic_1,
                    "color": "#000000",
                    "data": {"total": total_1, "definition": def_1},
                },
            }
        )

        nodes.append(
            {
                "key": topic_2,
                "attributes": {
                    "label": topic_2,
                    "color": "#000000",
                    "data": {"total": total_2, "definition": def_2},
                },
            }
        )

    json_data = {"nodes": nodes, "edges": edges}
    return json_data


# Topic Citation Interest
def get_topic_citation_interest_query(params):
    include_mesh_concepts = params.get("include_mesh_concepts")

    citations = []
    top_related_terms = []
    related_terms = {}

    # Add and format one concept at a time
    for concept in include_mesh_concepts:
        data = "%" + concept + "%"

        query = f"""
            SELECT t.pub_date as 'date', SUM(citation_count) as 'citation', GROUP_CONCAT(DISTINCT t.description) as 'related'
            FROM citation_stats as c
            JOIN topics as t ON t.pmid = c.pmid
            WHERE t.description LIKE %s AND t.pub_date BETWEEN '2022-05-01' AND '2022-8-31'
            GROUP BY t.pub_date
            ORDER BY t.pub_date;
            """

        result = execute(query, [data], show_query=False)

        # Getting date, and value of citations on that date & dictionary of count of related terms

        formatted_arr = []
        citation_sum = 0
        for data in result:
            citation_sum += int(data.get("citation"))
            formatted_arr.append(
                {"name": str(data.get("date")), "value": str(data.get("citation"))}
            )
            # Adding to related terms count
            for term in data.get("related").split(","):
                if related_terms.get(term) == None:
                    related_terms[term] = 1
                else:
                    related_terms[term] += 1

        citations.append(
            {
                "topic": concept,
                "total": citation_sum,
                "data": formatted_arr,
            }
        )

    for term in sorted(related_terms.items(), key=lambda x: x[1], reverse=True):
        top_related_terms.append({"name": term[0], "value": term[1]})

    return {"chart": citations, "related_terms": top_related_terms[0:5]}


#############
# MISC
#############


def get_autocomplete_files(replace=True):
    """
    Updates autocomplete JSON files from the database autocomplete tables.
    If <replace> is True, this will be done even if the file already exists.

    Tables are assumed to have two columns (concept_name, count), and be sorted in alphabetical order (case insensitive)
    """
    base_dir = "flask_app/home/static/autocomplete/"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    # (table_name, file_to_store_it_in)
    autocompletes = [
        ("umls_concept_autocomplete", "umls_concepts.json"),
        ("umls_relation_autocomplete", "umls_relations.json"),
        ("mesh_topic_autocomplete", "mesh_concepts.json"),
    ]

    for table, file in autocompletes:
        file = base_dir + file
        if not replace and os.path.exists(
            file
        ):  # if the file exists and replace not specified, skip it
            continue

        try:
            logging.info(f"Updating local file for table: {table}")
            result = db.query(f"SELECT * FROM {table} ORDER BY LOWER(concept_name)")
            result = [
                list(dic.values()) for dic in result
            ]  # create list of lists for each row
            with open(file, "w") as f:
                json.dump(result, f)
        except Exception as e:
            logging.error(
                f"Failed to retrieve autocomplete data from database. {e.__class__.__name__}: {e}"
            )


def search_paper_by_topic(topics, number):
    """Search a max number of a papers by having ALL the given list of topics"""
    query = f"""
    WITH any_terms AS (
        SELECT
            t.pmid as pmid,
            id.doi as doi,
            d.content as title,
            c.citation_count as citations,
            EXISTS(SELECT * FROM triples WHERE t.pmid = triples.pmid LIMIT 1) as triple
        FROM topics t
        JOIN documents d ON t.pmid = d.pmid
        JOIN id_map id ON t.pmid = id.pmid
        LEFT JOIN citation_stats c ON t.pmid = c.pmid
        WHERE d.content_type = "title"
        AND t.description IN ({', '.join('%s' for _ in topics)})
        GROUP BY t.description, pmid
        ORDER BY citations DESC
    )
    
    SELECT * FROM any_terms
    GROUP BY pmid
    HAVING COUNT(*) = {len(topics)}
    LIMIT %s
    """
    params = topics + [number]
    result = execute(query, params, show_query=False)
    for row in result:
        if row.get("doi"):
            row["doi"] = "https://doi.org/" + row["doi"]
    return result
