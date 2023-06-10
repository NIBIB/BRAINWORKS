from flask import current_app as app
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

import redshift_connector
class RedShiftDatabase():
    def __init__(self):
        self.connection_keywords = {
            'host': app.config['BRAINWORKS_DB_HOST'],
            'database': app.config['BRAINWORKS_DB_DATABASE'],
            'user': app.config['BRAINWORKS_DB_USER'],
            'password': app.config['BRAINWORKS_DB_PASSWORD'],
            'port': app.config['BRAINWORKS_DB_PORT']
        }

    def query(self, query, parameters=None, format='rows'):
        # Connect to the cluster
        conn = redshift_connector.connect(**self.connection_keywords)

        cur = conn.cursor()
        cur.execute(query, parameters)
        keys = [tup[0] for tup in cur.description]  # return column keys
        conn.commit()
        raw_rows = cur.fetchall()
        cur.close()
        conn.close()

        if format in ["cols", "pandas"]:
            columns = {k: [] for k in keys}
            for row in raw_rows:
                for i, key in enumerate(keys):
                    columns[key].append(row[i])
            if format == "cols":
                return columns
            else:  # pandas
                return pd.DataFrame(columns)
        elif format == "rows":  # rows
            rows = []
            for row in raw_rows:
                rows.append({keys[i]: row[i] for i in range(len(keys))})
            return rows
        else:
            logging.info("Format not recognized")
            return
db = RedShiftDatabase()


def execute(query, params=[], raise_no_results=True, show_query=False):
    """execute the given query"""
    if show_query:
        logging.info(query)
        logging.info("Params: ", params)

    try:
        result = db.query(query, parameters=params)
    except redshift_connector.error.ProgrammingError as e:
        logging.exception(e)
        raise Exception("Critical error in database query. This error has been logged.")
    except redshift_connector.error.DatabaseError as e:
        logging.exception(e)
        raise Exception("Unable to connect to the database. This likely means that the database is temporarily unavailable - please try again later.")
    except Exception as e:
        logging.exception(e)
        raise Exception("Uncaught Database Error.")
    if raise_no_results and len(result) == 0:
        raise Exception("Your query returned no results. Try reducing the specificity of your search")
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
            f"AND LOWER({column}) IN ({','.join('%s' for _ in params['include_concepts'])})"
        )
        data += [p.lower() for p in params["include_concepts"]]
    return terms


def filter_exclude_concepts(params, data, column):
    terms = ""
    if params.get("exclude_concepts"):
        terms += (
            f" AND LOWER({column}) IN ({','.join('%s' for _ in params['exclude_concepts'])})"
        )
        data += [p.lower() for p in params["exclude_concepts"]]
    return terms


def filter_relations(params, data, column):
    """create the WHERE clause to filter a SQL query by relation search terms"""
    terms = ""
    if params.get("include_relations"):
        terms += (
            f"AND LOWER({column}) IN ({','.join('%s' for _ in params['include_relations'])})"
        )
        data += [p.lower() for p in params["include_relations"]]

    if params.get("exclude_relations"):
        terms += f" AND LOWER({column}) NOT IN ({','.join('%s' for _ in params['exclude_relations'])})"
        data += [p.lower() for p in params["exclude_relations"]]

    return terms


def filter_projects(params, data):
    """Create a WHERE statement o filter by the projects table"""
    if params.get("grants"):
        if params.get("grants") == 'obssr':
            return f"""JOIN obssr_project_numbers o ON o."project number" = p.full_project_num AND o."sub project #" = p.subproject_id"""
        else:  # other grant specified
            return ""
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

    # set system variable for max allowed recursion

    query = f"""
WITH
filtered_citations AS (
    SELECT c.pmid, g.citedby, g.citation_date, DENSE_RANK() OVER(ORDER BY c.pmid) as parent_id  -- track parent PMID of each citation chain
    FROM concepts c
    JOIN citation_graph g ON g.pmid = c.pmid
    WHERE concept_type IN ('subject', 'object')
    {filter_include_concepts(params, data, 'concept_name')}
    GROUP BY c.pmid, g.citedby, g.citation_date
    LIMIT 15
)

, l1 AS (
    SELECT f.pmid, f.citedby, f.citation_date, parent_id, 0 as depth
        FROM filtered_citations f
    UNION ALL
    SELECT c.pmid, c.citedby, c.citation_date, parent_id, 1 as depth
        FROM filtered_citations f
        JOIN citation_graph c ON f.citedby = c.pmid
)

, l2 AS (
    SELECT f.pmid, f.citedby, f.citation_date, parent_id, depth
        FROM l1 f
    UNION ALL
    SELECT c.pmid, c.citedby, c.citation_date, parent_id, 2 as depth
        FROM l1 f
        JOIN citation_graph c ON f.citedby = c.pmid
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
    SELECT *
    FROM unique_citations c
    JOIN parent_size s ON s.parent_id = c.parent_id
    ORDER BY c.parent_id, depth
    LIMIT 500
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
        FROM paper_info
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
        info = papers[target_pmid]

        doi = ""
        if info["doi"]:
            doi = "https://doi.org/" + info["doi"]

        title = info["pub_title"] or "title unavailable"
        depth = info.get("depth", max_depth)

        pub_date = info["pub_date"]
        pub_date = datetime(year=pub_date.year, month=pub_date.month, day=pub_date.day).timestamp()

        authors = ""
        if info["authors"]:
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
                            "title": info["pub_title"],
                            "authors": authors,
                            "abstract": info["abstract"],
                            "journal_title": info["journal_title"],
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

    limit = int(params.get('limit', 200))

    # main query
    query = "WITH "

    query += f"""
    included_concepts AS (
        SELECT pmid, triple_id, concept_id
        FROM triples_filtered_relations_concepts c
        WHERE concept_type IN ('subject', 'object')
        {filter_include_concepts(params, data, 'concept_name')}
    )
    """

    if if_exclude_concepts:
        query += f"""
        , excluded_concepts AS (
            SELECT pmid, triple_id, concept_id
            FROM triples_filtered_relations_concepts c
            WHERE concept_type IN ('subject', 'object')
            {filter_exclude_concepts(params, data, 'concept_name')}
        )
        """

    query += f"""
    -- triples that include/exclude the given concepts
    , filtered_triples AS (
        SELECT DISTINCT t.pmid, t.triple_id
        FROM triples t
        JOIN included_concepts ci ON t.pmid = ci.pmid AND t.triple_id = ci.triple_id
        JOIN citation_stats s ON s.pmid = t.pmid
        {"LEFT JOIN excluded_concepts ce ON t.pmid = ce.pmid AND t.triple_id = ce.triple_id WHERE ce.concept_id is NULL" if if_exclude_concepts else ''}
        ORDER BY s.relative_citation_ratio DESC NULLS LAST
        LIMIT {int(limit/3)}
    )

    -- ALL concepts associated with the filtered triples, not including the ones searched for. These are the second-order concepts.
    , l1 AS (
        SELECT DISTINCT c.concept_id
        FROM filtered_triples t
        JOIN triples_filtered_relations_concepts c ON t.pmid = c.pmid AND t.triple_id = c.triple_id AND c.concept_type != 'relation'
        LEFT JOIN included_concepts ci ON ci.pmid = c.pmid AND ci.triple_id = c.triple_id AND ci.concept_id = c.concept_id 
        WHERE ci.pmid IS NULL
    )
    
    -- Get triples that have those second order concepts
    , l2 AS (
        SELECT c.pmid, c.triple_id, c.concept_id, s.relative_citation_ratio
        FROM l1
        JOIN triples_filtered_relations_concepts c ON l1.concept_id = c.concept_id AND c.concept_type != 'relation'
        JOIN citation_stats s ON c.pmid = s.pmid
        ORDER BY s.relative_citation_ratio DESC NULLS LAST
        LIMIT {int(limit/3)}
    )
    
    , l3 AS (
        SELECT DISTINCT c.pmid, c.triple_id
        FROM l2
        JOIN triples_filtered_relations_concepts c ON l2.concept_id = c.concept_id AND c.concept_type != 'relation'
        JOIN citation_stats s ON c.pmid = s.pmid
        ORDER BY s.relative_citation_ratio DESC NULLS LAST
        LIMIT {int(limit/3)}
    )
    
    -- combine original triples with second order triples
    , combine AS (
        SELECT * FROM filtered_triples
        UNION ALL
        SELECT pmid, triple_id FROM l2
        UNION ALL
        SELECT pmid, triple_id FROM l3
    )

    SELECT *
    FROM triple_graph tg 
    JOIN combine c ON tg.pmid = c.pmid AND tg.triple_id = c.triple_id
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
    params = all_concept_ids * 3
    concept_query = f"""
    WITH 
    
    concepts AS (
        SELECT 
            c.concept_id as CUI,
            ANY_VALUE(concept_name) as concept_name 
        FROM triples_filtered_relations_concepts c
        WHERE c.concept_id IN ({placeholders})
        GROUP BY c.concept_id
    )
    
    , defs AS (
        SELECT CUI, MAX(DEF) as DEF FROM definitions d
        WHERE CUI IN ({placeholders})
        AND d.DEF is not NULL
        GROUP BY CUI
    )
    
    SELECT c.CUI as CUI, c.concept_name as name, d.DEF as definition
    FROM concepts c
    LEFT JOIN defs d ON c.CUI = d.CUI
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
    concepts = {c["cui"]: c for c in concepts}

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
        topic_ids = df3.iloc[ii]["subject_umls_topics"].split(";")  # if ii is not 0 else None
        node_map[node] = topic_ids
        for id in topic_ids:
            topic_map[id] = topic_map.get(id, 0) + 1  # increment topic count

    center_cluster_topic = list(topic_map.keys())
    center_cluster_topic.sort(key=lambda k: topic_map[k])
    center_cluster_topic = center_cluster_topic[-1]
    cluster_map = {}  # map of topics to number of nodes in that cluster. Used to eliminate clusters with a low number of nodes.

    # now loop through again and assign node data
    for node, cnt in raw_nodes.items():
        # date
        dt = min_dates[node]
        timestamp = datetime(year=dt.year, month=dt.month, day=dt.day).timestamp()
        node_data = {"time": timestamp}

        # topics
        node_map[node].sort(reverse=True, key=lambda id: topic_map[id])  # sort node topics by frequency
        node_concepts = []  # list of concepts for this node

        # increment the number of nodes in the cluster (given by the largest frequency topic)
        cluster_map.update({node_map[node][0]: cluster_map.get(node_map[node][0],0)+1})

        for i, id in enumerate(node_map[node]):  # assign node data in that order
            concept = concepts.get(id)  # get the concept for this id
            name, definition = "", ""
            if concept:
                node_concepts.append(concept)
                name = concept["name"]
                definition = concept["definition"]
            node_data[f"topic-{i+1}"] = name
            node_data[f"definition-{i+1}"] = definition

        node = {"key": node, "attributes": {"label": node, "data": node_data}}
        nodes.append(node)

    edge_map = ({})  # map of source nodes and target nodes. Used to keep track of how many of each edge was added
    edge_nodes = set()  # set of all nodes that edges connect to. Used to track nodes that don't have any edges.
    for i, triple in enumerate(triples):
        # creating the date object of today's date
        if triple["doi"]:
            doi = "https://doi.org/" + triple["doi"]
        else:
            doi = ""

        pub_date = triple["pub_date"]
        timestamp = datetime(year=pub_date.year, month=pub_date.month, day=pub_date.day).timestamp()

        source = triple["subject"]
        target = triple["object"]

        # if either node is in the center cluster
        if node_map[source][0] == center_cluster_topic or node_map[target][0] == center_cluster_topic:
            if cluster_map[node_map[source][0]] == 1 or cluster_map[node_map[target][0]] == 1:
                continue  # don't add this edge

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

        edge_nodes.add(source)
        edge_nodes.add(target)

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


    # remove all nodes without edges
    new_nodes = []
    for node in nodes:
        if node['key'] in edge_nodes:
            new_nodes.append(node)
    nodes = new_nodes

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
        "settings": {"cluster_level": 1},
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
            "Improve",
            "Improved",
            "Improvement",
            "Improving (qualifier value)",
            "Positive",
            "Enhance (action)",
            "Promotion (action)",
            "Induce (action)",
            "Treating",
            "Benefit"
        ]:
            score += 1
        elif relation in [
            "Decrease",
            "Decreased",
            "Reduced",
            "Suppressed",
            "inhibited",
            "Negative",
            "Removed",
            "Impaired",
            'Inhibition',
            'Decreasing',
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
    pmid = params.get("pmid").strip()  # really this could be a pmid or pub title
    pub_query = f"""
        SELECT *
        FROM paper_info
        WHERE pmid = %s
        LIMIT 1
    """

    data = execute(pub_query, [pmid, pmid])[0]
    data = {
        "pmid": data["pmid"],
        "pub_title": data["pub_title"] or "[title unavailable]",
        "doi": "https://doi.org/" + data["doi"] if data["doi"] else "",
        "authors": (", ").join(data["authors"].split(";")) if data["authors"] else "[authors unavailable]",
        "projects": data.get('projects') or "",
        "pub_date": data["pub_date"],
        "abstract": data["abstract"] or ""
    }

    # triples
    triple_query = f"""
    WITH
    -- This makes sure the unique concepts are pulled.
    -- technically they should already be unique in the database, but this is just in case
    concepts AS (
        SELECT
            ANY_VALUE(c.pmid) as pmid,
            ANY_VALUE(c.id) as id,
            ANY_VALUE(c.total_concepts) as total_concepts,
            c.triple_id,
            c.concept_name,
            c.concept_type,
            c.concept_id,
            c.start_char,
            c.end_char,
            c.frag_start_char,
            c.frag_end_char
        FROM concepts c
        WHERE pmid = %s
        GROUP BY c.triple_id, c.concept_type, c.concept_name, c.concept_id, c.start_char, c.end_char, c.frag_start_char, c.frag_end_char
    )
    
    SELECT 
        t.subject,
        t.relation,
        t.object,
        ANY_VALUE(t.sentence_number) as sentence_number,
        ANY_VALUE(t.start_char) as start_char,
        ANY_VALUE(t.end_char) as end_char,
        LISTAGG(DISTINCT cs.id, ';') as subject_umls_topics,
        LISTAGG(DISTINCT co.id, ';') as object_umls_topics
    FROM triples t
    JOIN concepts cs ON cs.pmid = t.pmid AND cs.triple_id = t.triple_id AND cs.concept_type = 'subject' AND cs.concept_name IS NOT NULL
    JOIN concepts co ON co.pmid = t.pmid AND co.triple_id = t.triple_id AND co.concept_type = 'object'  AND co.concept_name IS NOT NULL
    GROUP BY subject, relation, object
    ORDER BY (ANY_VALUE(cs.total_concepts) + ANY_VALUE(co.total_concepts)) DESC
"""
    triples = execute(triple_query, [pmid], raise_no_results=False)
    df = pd.DataFrame(triples)
    zip_data = create_zip(df)  # create base-64 encoded zip file

    all_concept_ids = [
        id for t in triples for id in t["subject_umls_topics"].split(";")
    ] + [id for t in triples for id in t["object_umls_topics"].split(";")]

    concepts = {}
    if len(all_concept_ids):  # if any concepts found for this paper
        concept_query = f"""
            SELECT 
                c.id,
                ANY_VALUE(c.start_char) as start_char,
                ANY_VALUE(c.end_char) as end_char,
                ANY_VALUE(c.frag_start_char) as frag_start_char,
                ANY_VALUE(c.frag_end_char) as frag_end_char,
                ANY_VALUE(d.DEF) as definition
            FROM concepts c
            LEFT JOIN definitions d ON c.concept_id = d.CUI
            WHERE c.id IN ({','.join(['%s' for _ in all_concept_ids])})
            GROUP BY c.id, d.CUI
        """
        concepts = execute(concept_query, all_concept_ids)
        concepts = {int(c["id"]): c for c in concepts}

    # highlight text
    # data['abstract'] = highlight_abstract(data['abstract'], triples)
    data["abstract"] = abstract_into_list(data["abstract"], triples)

    # parse triple information
    for triple in triples:
        triple["subject_topics"] = [
            concepts.get(int(id)) for id in triple["subject_umls_topics"].split(";")
        ]
        triple["object_topics"] = [
            concepts.get(int(id)) for id in triple["object_umls_topics"].split(";")
        ]

    return data, triples, zip_data


# Topic co-occurrences
def topic_co_occurrences_query(params):
    include_mesh_concepts = params.get("include_mesh_concepts")
    exclude_mesh_concepts = params.get("exclude_mesh_concepts")
    limit = min(int(params.get("limit",200)), 1000)

    include_placeholders = ','.join(['%s' for _ in include_mesh_concepts])
    if exclude_mesh_concepts:
        exclude_placeholders = ','.join(['%s' for _ in exclude_mesh_concepts])
    else:
        exclude_mesh_concepts = ['']
        exclude_placeholders = '%s'

    branches = 10
    top_n = int(limit/(2*branches))

    data = include_mesh_concepts*2 + exclude_mesh_concepts*2 + (include_mesh_concepts + exclude_mesh_concepts)*4

    query = f"""
    WITH 
results AS (
    SELECT 
        topic_1, topic_2,
        total_1, total_2,
        def_1, def_2,
        cat_1, cat_2,
        perc_1, perc_2,
        "delta", delta_percentile,
        frequency, frequency_percentile, 
        total, total_percentile,
        importance, importance_percentile,
        relevance, avg_prob,
        ROW_NUMBER() OVER(PARTITION BY topic_1 ORDER BY delta_percentile DESC) AS delta_order,
        ROW_NUMBER() OVER(PARTITION BY topic_1 ORDER BY frequency_percentile DESC) AS frequency_order,
        ROW_NUMBER() OVER(PARTITION BY topic_1 ORDER BY importance_percentile DESC) AS importance_order
    FROM topic_co_occurrence_graph
    WHERE (topic_1 IN ({include_placeholders}) OR topic_2 IN ({include_placeholders}))
    AND topic_2 NOT IN ({exclude_placeholders}) AND topic_1 NOT IN ({exclude_placeholders})
)

-- going from the search terms out
, away AS (
    SELECT * FROM results WHERE topic_1 IN ({include_placeholders}) AND topic_2 NOT IN ({exclude_placeholders})
)

-- top n co-occurrences with each searched topic
, top_n_to AS (
    SELECT * FROM (  -- largest positive delta
        SELECT * FROM away ORDER BY "delta" DESC LIMIT 1
    ) 
    UNION ALL 
    SELECT * FROM (  -- largest negative delta
        SELECT * FROM away ORDER BY "delta" ASC LIMIT 1
    )
    UNION ALL
    SELECT * FROM away WHERE (importance_order <= {top_n} OR frequency_order <= {top_n})  -- top 10 importance and top 10 fequencies
)

--SELECT * FROM top_n_to;

-- top n co-occurrences where the searched topics was at the top in frequency
, top_n_from AS (
    SELECT * FROM results
    WHERE topic_2 IN ({include_placeholders}) AND topic_1 NOT IN ({exclude_placeholders})
    ORDER BY frequency_order ASC
    LIMIT {top_n}
)

--SELECT * FROM top_n_from;

-- second-order edges from the top_n_to nodes
, l2_to AS (
    SELECT
        g.topic_1, g.topic_2,
        g.total_1, g.total_2,
        g.def_1, g.def_2,
        g.cat_1, g.cat_2,
        g.perc_1, g.perc_2,
        g."delta", g.delta_percentile,
        g.frequency, g.frequency_percentile, 
        g.total, g.total_percentile,
        g.importance, g.importance_percentile,
        g.relevance, g.avg_prob,
        ROW_NUMBER() OVER(PARTITION BY g.topic_1 ORDER BY g.delta_percentile DESC) AS delta_order,
        ROW_NUMBER() OVER(PARTITION BY g.topic_1 ORDER BY g.frequency_percentile DESC) AS frequency_order,
        ROW_NUMBER() OVER(PARTITION BY g.topic_1 ORDER BY g.importance_percentile DESC) AS importance_order
    FROM topic_co_occurrence_graph g
    JOIN top_n_to n ON n.topic_2 = g.topic_1
    WHERE g.topic_2 NOT IN ({include_placeholders})
    AND g.topic_2 NOT IN ({exclude_placeholders})
)

-- second-order edges from the top_n_from nodes
, l2_from AS (
    SELECT
        g.topic_1, g.topic_2,
        g.total_1, g.total_2,
        g.def_1, g.def_2,
        g.cat_1, g.cat_2,
        g.perc_1, g.perc_2,
        g."delta", g.delta_percentile,
        g.frequency, g.frequency_percentile, 
        g.total, g.total_percentile,
        g.importance, g.importance_percentile,
        g.relevance, g.avg_prob,
        ROW_NUMBER() OVER(PARTITION BY g.topic_1 ORDER BY g.delta_percentile DESC) AS delta_order,
        ROW_NUMBER() OVER(PARTITION BY g.topic_1 ORDER BY g.frequency_percentile DESC) AS frequency_order,
        ROW_NUMBER() OVER(PARTITION BY g.topic_1 ORDER BY g.importance_percentile DESC) AS importance_order
    FROM topic_co_occurrence_graph g
    JOIN top_n_from n ON n.topic_1 = g.topic_1
    WHERE g.topic_2 NOT IN ({include_placeholders}) AND g.topic_2 NOT IN ({exclude_placeholders})
)

-- combine all
, a AS (
    SELECT * FROM top_n_to
    UNION ALL
    SELECT * FROM top_n_from
    UNION ALL
    SELECT * FROM l2_to WHERE l2_to.importance_order <= {branches}
    UNION ALL
    SELECT * FROM l2_from WHERE l2_from.importance_order <= {branches}
)

--SELECT * FROM a;

-- third-order edges, which could connect second-order nodes to new nodes or first-order nodes.
, l3 AS (
    SELECT
        g.topic_1, g.topic_2,
        g.total_1, g.total_2,
        g.def_1, g.def_2,
        g.cat_1, g.cat_2,
        g.perc_1, g.perc_2,
        g."delta", g.delta_percentile,
        g.frequency, g.frequency_percentile, 
        g.total, g.total_percentile,
        g.importance, g.importance_percentile,
        g.relevance, g.avg_prob,
        ROW_NUMBER() OVER(PARTITION BY g.topic_1 ORDER BY g.delta_percentile DESC) AS delta_order,
        ROW_NUMBER() OVER(PARTITION BY g.topic_1 ORDER BY g.frequency_percentile DESC) AS frequency_order,
        ROW_NUMBER() OVER(PARTITION BY g.topic_1 ORDER BY g.importance_percentile DESC) AS importance_order
    FROM topic_co_occurrence_graph g
    WHERE (g.topic_1 IN (SELECT topic_1 FROM a) OR g.topic_1 IN (SELECT topic_2 FROM a))
    AND (g.topic_2 IN (SELECT topic_1 FROM a) OR g.topic_2 IN (SELECT topic_2 FROM a))
)

--SELECT * FROM (SELECT * FROM l3 WHERE importance_order = 1)
--UNION ALL
SELECT * FROM a;

    """
    pairs = execute(query, data)
    return pairs


def get_topic_co_occurrences(params):
    # update_topic_co_occurrence_table()
    pairs = topic_co_occurrences_query(params)

    dates = execute("SELECT * FROM topic_co_occurrence_graph_dates")[0]
    start_date = dates['start'].strftime("%Y/%m")
    end_date = dates['end'].strftime("%Y/%m")

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
        total_1 = float(row["total_1"])  # current absolute total occurrences of topic_1
        total_2 = float(row["total_2"])  # current absolute total occurrences of topic_2
        perc_1 = float(row['perc_1'])*100  # percentile
        perc_2 = float(row['perc_2'])*100
        cat_1 = row['cat_1']  # MeSH high-level hierarchy node
        cat_2 = row['cat_2']
        def_1 = row.get("def_1")  # definition
        def_2 = row.get("def_2")

        delta = float(row["delta"])*100  # % change in frequency
        delta_percentile = float(row['delta_percentile'])*100
        total = float(row['total'])  # total pair occurrences
        total_percentile = float(row['total_percentile'])*100
        frequency = float(row["frequency"])  # current proportional frequency
        frequency_percentile = float(row['frequency_percentile'])*100

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
                        "delta_percentile": delta_percentile,
                        "total": total,
                        "total_percentile": total_percentile,
                        "frequency": frequency,
                        "frequency_order": frequency_order,
                        "frequency_percentile": frequency_percentile,
                        "start_date": start_date,
                        "end_date": end_date
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
                        "data": {"total": total_1, "definition": def_1, "category": cat_1, "percentile": perc_1, "start_date": dates['start'], "end_date": dates['end']},
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
                        "data": {"total": total_2, "definition": def_2, "category": cat_2, "percentile": perc_2, "start_date": start_date, "end_date": end_date},
                    },
                }
            )
            added_nodes.add(topic_2)

    # the config dict to pass to the graph API
    config = {
        "maps": {
            "node_size": {"data": "percentile", "min": 5, "max": 20},
            "node_color": {"data": "category", "map": {
                'Diseases': "#a6d75b",
                'Organisms': '#24a824',
                'Anatomy': '#2e9e84',
                'Humanities': '#54bebe',
                'Human Groups': "#007399",
                'Social Phenomena': '#005df9',
                'Psychiatry and Psychology': "#1a8cdd",
                'Phenomena and Processes': "#8184fb",
                'Techniques and Equipment': "#766aaf",
                'Chemicals and Drugs': "#ab3da9",
                'Health Care': '#d65c81',
                'Information Science': "#fe5a01",
                'Technology, Industry, and Agriculture': "#eeb711",
                'Disciplines and Occupations': "#ece000",
                'Geographicals': "#814a0c",
                'Other': "#503f3f",
            }},
            "edge_size": {"data": "frequency_percentile", "min": 5, "max": 15},
            "edge_color": {
                "data": "delta",
                "map": {"mid": 0, "colors": ["#cf1717", "#e6e6e6", "#5370c6"]},
            },
        },
        "filters": {  # sliders
            # "Delta Order": {"type": "edge", "data": "delta_order"},
            "Topic Occurrence Percentile": {"type": "node", "data": "percentile"},
            "Pair Co-Occurrence Percentile": {"type": "edge", "data": "frequency_percentile"},
        },
        "settings": {"edge_filters_hide_nodes": True},
    }

    graph = {"nodes": nodes, "edges": edges}
    json_data = {"graph": graph, "config": config}
    return json_data, zip_data


def get_extra_topic_co_occurrences(topic, start, num, session):
    """
    Get extra topics to add to the co-occurrence graph.
    <start> is the starting row to return
    <num> is the number of rows to return
    """

    # get parameters made with the original query
    params = session.get('tool_topic_co_occurrences_form')

    include_mesh_concepts = params.get("include_mesh_concepts")
    exclude_mesh_concepts = params.get("exclude_mesh_concepts")
    data = []  # injected parameters for the query

    # pick the right pre-computed table for filtering grants
    if params.get('grants') == 'obssr':
        table = "topic_co_occurrence_graph_obssr"
    else:
        table = "topic_co_occurrence_graph"

    # SQL query WHERE statements
    exclude_topics_where = ""

    # we don't use the include_topics constraint of the original query because it would only return what's already there. This is looking for new connections.
    include_topics_where = f"WHERE topic_1 = %s"
    data += [topic]

    if exclude_mesh_concepts:
        s = ", ".join("%s" for _ in exclude_mesh_concepts)  # placeholders
        exclude_topics_where = (f"AND (topic_1 NOT IN ({s}) AND topic_2 NOT IN ({s}))")
        data += exclude_mesh_concepts  # twice because the list is in the query twice
        data += exclude_mesh_concepts

    query = f"""
    WITH results AS (
        SELECT 
        topic_1, topic_2,
        total_1, total_2,
        def_1, def_2,
        cat_1, cat_2,
        perc_1, perc_2,
        "delta", delta_percentile,
        frequency, frequency_percentile, 
        total, total_percentile,
        importance, importance_percentile,
        relevance, avg_prob,
        ROW_NUMBER() OVER(PARTITION BY topic_1 ORDER BY delta_percentile DESC) AS delta_order,
        ROW_NUMBER() OVER(PARTITION BY topic_1 ORDER BY frequency_percentile DESC) AS frequency_order,
        ROW_NUMBER() OVER(PARTITION BY topic_1 ORDER BY importance_percentile DESC) AS importance_order
        FROM {table}
        {include_topics_where}
        {exclude_topics_where}
    )
    
    SELECT * FROM results ORDER BY frequency_order
    LIMIT {num} OFFSET {max(0,start-1)}
    """
    pairs = execute(query, data, raise_no_results=False)

    nodes, added_nodes = [], set()
    edges, edge_map = [], {}  # map of edges to keep track of duplicate combinations

    for row in pairs:
        # some results need to be converted from the weird SQL decimal type to regular float
        topic_1 = row["topic_1"]
        topic_2 = row["topic_2"]
        total_1 = float(row["total_1"])  # current absolute total occurrences of topic_1
        total_2 = float(row["total_2"])  # current absolute total occurrences of topic_2
        perc_1 = float(row['perc_1'])*100  # percentile
        perc_2 = float(row['perc_2'])*100
        cat_1 = row['cat_1']  # MeSH high-level hierarchy node
        cat_2 = row['cat_2']
        def_1 = row.get("def_1")  # definition
        def_2 = row.get("def_2")

        delta = float(row["delta"])*100  # % change in frequency
        delta_percentile = float(row['delta_percentile'])*100
        total = float(row["total"])  # total pair occurrences
        total_percentile = float(row['total_percentile']) * 100
        frequency = float(row["frequency"])  # current proportional frequency
        frequency_percentile = float(row['frequency_percentile'])*100

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
                        "delta_percentile": delta_percentile,
                        "total": total,
                        "total_percentile": total_percentile,
                        "frequency": frequency,
                        "frequency_order": frequency_order,
                        "frequency_percentile": frequency_percentile
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
                    "data": {"total": total_1, "definition": def_1, "category": cat_1, "percentile": perc_1},
                },
            }
        )

        nodes.append(
            {
                "key": topic_2,
                "attributes": {
                    "label": topic_2,
                    "color": "#000000",
                    "data": {"total": total_2, "definition": def_2, "category": cat_2, "percentile": perc_2},
                },
            }
        )

    json_data = {"nodes": nodes, "edges": edges}
    return json_data


# Topic Citation Interest
def get_topic_citation_interest_query(params):
    include_mesh_concepts = params.get("include_mesh_concepts")

    citations = []

    # Add and format one concept at a time
    for concept in include_mesh_concepts:
        data = "%" + concept + "%"

        query = f"""
            SELECT t.pub_date as 'date', SUM(citation_count) as 'citation'
            FROM citation_stats as c
            JOIN topics as t ON t.pmid = c.pmid
            WHERE t.description LIKE %s AND t.pub_date BETWEEN '2022-05-01' AND '2022-8-31'
            GROUP BY t.pub_date
            ORDER BY t.pub_date;
            """

        result = execute(query, [data])

        formatted_arr = []
        citation_sum = 0
        for data in result:
            citation_sum += int(data.get("citation"))
            formatted_arr.append(
                {"name": str(data.get("date")), "value": str(data.get("citation"))}
            )

        citations.append(
            {"topic": concept, "total": citation_sum, "data": formatted_arr}
        )

    return citations


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
