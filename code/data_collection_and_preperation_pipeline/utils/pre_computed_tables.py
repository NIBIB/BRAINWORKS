from utils.base import Base
from utils.database.database import RedShiftDatabase

from datetime import date, timedelta

class PreComputedTables(Base):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = RedShiftDatabase(self.config)

    def all(self):
        """ Create all tables """
        tables = []
        tables.extend(self.paper_info())
        tables.extend(self.topic_co_occurrence_graph())
        tables.extend(self.citation_graph())
        tables.extend(self.triple_graph())
        tables.extend(self.autocomplete_tables())
        return tables

    def UMLS(self):
        """ Create and load UMLS tables from S3 """

        self.log("Loading 'definitions' table...")
        self.db.query("DROP TABLE IF EXISTS definitions")
        self.db.query(f"""
        CREATE TABLE definitions (
            CUI	char(8),
            AUI	varchar(9),
            ATUI	varchar(11),
            SATUI	varchar(50),
            SAB	varchar(40),
            DEF	varchar(65535),
            SUPPRESS char(1),
            CVF	bigint
        )
        """)
        self.db.query(f"""
            COPY definitions
            FROM 's3://{self.config.s3_bucket}/MRDEF.RRF' 
            iam_role '{self.config.redshift.iam_s3_access_role}'
            DELIMITER AS '|'
        """)
        self.log('done')

        self.log("Loading 'concept_map' table...")
        self.db.query("DROP TABLE IF EXISTS concept_map")
        self.db.query(f"""
        CREATE TABLE concept_map (
            CUI	char(8),
            LAT	char(3),
            TS	char(1),
            LUI	varchar(10),
            STT	varchar(3),
            SUI	varchar(10),
            ISPREF	char(1),
            AUI	varchar(9),
            SAUI	varchar(50),
            SCUI	varchar(100),
            SDUI	varchar(100),
            SAB	varchar(40),
            TTY	varchar(40),
            CODE	varchar(100),
            STR	varchar(65535),
            SRL	bigint,
            SUPPRESS char(1),
            CVF	bigint
        )
        """)
        self.db.query(f"""
            COPY concept_map
            FROM 's3://{self.config.s3_bucket}/MRCONSO.RRF' 
            iam_role '{self.config.redshift.iam_s3_access_role}'
            DELIMITER AS '|'
        """)
        self.log('done')

        self.log("Loading 'MRHIER', table...")
        self.db.query("DROP TABLE IF EXISTS MRHIER")
        self.db.query(f"""
        CREATE TABLE MRHIER (
            CUI	char(8),
            AUI	varchar(9),
            CXN	int,
            PAUI varchar(10),
            SAB	varchar(40),
            RELA varchar(100),
            PTR	varchar(65535),
            HCD	varchar(100),
            CVF	int
        )
        """)
        self.db.query(f"""
            COPY MRHIER
            FROM 's3://{self.config.s3_bucket}/MRHIER.RRF' 
            iam_role '{self.config.redshift.iam_s3_access_role}'
            DELIMITER AS '|'
        """)
        self.log('done')

    def paper_info(self):
        """ Table of all publications with all needed info for other tables """
        self.log("Creating Paper Info table...")
        self.db.query("DROP TABLE IF EXISTS paper_info")
        self.db.query(f"""
CREATE TABLE paper_info AS

WITH
formatted_affiliations AS (
    SELECT 
        a.pmid,
        LISTAGG(DISTINCT a.first_name || ' ' || a.last_name, ';') WITHIN GROUP (ORDER BY a.affiliation_num ASC) as authors
    FROM affiliations a
    GROUP BY a.pmid
)

, formatted_projects AS (
    SELECT
        l.pmid,
        LISTAGG(DISTINCT l.project_number, ', ') as projects
    FROM link_tables l
    GROUP BY l.pmid
)

SELECT
    p.pmid,
    p.pub_title,
    p.journal_title,
    p.pub_date,
    id.doi,
    a.authors,
    l.projects,
    d.content as abstract
FROM publications p
LEFT JOIN formatted_affiliations a ON a.pmid = p.pmid
JOIN id_map id ON id.pmid = p.pmid
JOIN documents d ON d.pmid = p.pmid AND d.content_type = 'abstract'
LEFT JOIN formatted_projects l ON l.pmid = p.pmid
""")
        return ["paper_info"]

    def topic_co_occurrence_graph(self, delta=90):
        """ Build topic co-occurrence graph (for the last two months, by default) """

        self.log("Creating 'mesh_excluded_terms', table...")
        self.db.query("DROP TABLE IF EXISTS mesh_excluded_terms")
        self.db.query(f"""
        CREATE TABLE mesh_excluded_terms AS
            SELECT m.code as id, ANY_VALUE(m.str) as name
            FROM concept_map m
            JOIN MRHIER h ON h.cui = m.cui AND h.aui = m.aui AND m.sab = 'MSH'
            WHERE ptr LIKE '%.A0957610%'  -- study types
            OR ptr LIKE '%.A0055143%'  -- study types
            OR ptr LIKE '%.A2369583%' -- study types
            OR ptr LIKE '%.A0861160%'  -- Age groups
            OR ptr LIKE '%.A0112632%'  -- Risk
            OR ptr LIKE '%.A2364231%'  -- Male, Female
            GROUP BY id
        """)
        self.log('done')

        now = date.today()
        now = date(year=2022, month=11, day=1)
        delta = timedelta(days=delta)

        time_3 = now
        time_2 = now - delta
        time_1 = now - delta - delta

        time_1 = date(year=time_1.year, month=time_1.month, day=1)
        time_2 = date(year=time_2.year, month=time_2.month, day=1)
        time_3 = date(year=time_3.year, month=time_3.month, day=1)

        time_1 = str(time_1)
        time_2 = str(time_2)
        time_3 = str(time_3)

        self.db.query("DROP TABLE IF EXISTS topic_co_occurrence_graph_dates")
        self.db.query(f"CREATE TABLE topic_co_occurrence_graph_dates AS SELECT * FROM (SELECT '{time_1}'::DATE as start, '{time_3}'::DATE as end)")

        self.log(f"Creating Topic Co-Occurrence Table... ({time_1} - {time_3})")

        self.db.query("DROP TABLE IF EXISTS topic_co_occurrence_graph")
        self.db.query(f"""
CREATE TABLE topic_co_occurrence_graph AS
WITH 

vars AS (
SELECT 
   '{time_1}'::DATE AS t1,
   '{time_2}'::DATE AS t2,
   '{time_3}'::DATE AS t3
)


--Clean up topics table (removing duplicate topics from individual papers, prune mesh hierarchy)
, topics AS (
    SELECT 
        t.pmid, 
        ANY_VALUE(pub_date) as pub_date, 
        ANY_VALUE(topic_id) as id,
        description as topic
    FROM topics t
    LEFT JOIN mesh_excluded_terms ex ON t.topic_id = ex.id
    WHERE ex.id is NULL
    GROUP BY description, t.pmid
)


-- Pairs from time range A

-- counts for each pair
, pairs_a_counts AS ( 
    SELECT distinct
        t1.topic as topic_1,
        t2.topic as topic_2,
        COUNT(*) as cnt
    FROM topics t1
    JOIN topics t2 on t2.pmid = t1.pmid AND t1.topic != t2.topic
    WHERE t1.pub_date > (SELECT t1 FROM vars) AND t1.pub_date <= (SELECT t2 from vars)
    GROUP BY topic_1, topic_2
    HAVING cnt >= 5
)

--SELECT topic_1, topic_2, cnt FROM pairs_a_counts ORDER BY cnt DESC;

-- sum of all pair counts (single number)
, pairs_a_sum AS (
    SELECT 
        SUM(cnt)/2 as sum
    FROM pairs_a_counts
)

-- count of unique pairs (single number)
, pairs_a_unique AS (
    SELECT COUNT(*)/2 as pairs
    FROM pairs_a_counts
)

-- put it all in one table
, pairs_a AS (
    SELECT 
        topic_1, topic_2, cnt::DECIMAL, sum::DECIMAL, pairs
    FROM pairs_a_counts
    CROSS JOIN pairs_a_sum
    CROSS JOIN pairs_a_unique
)

--SELECT (pa.cnt::DECIMAL/pa.sum::DECIMAL) as t FROM pairs_a pa;

-- Pairs for time range B

-- counts for each pair
, pairs_b_counts AS ( 
SELECT distinct
        t1.topic as topic_1,
        t2.topic as topic_2,
        COUNT(*) as cnt
    FROM topics t1  
    JOIN topics t2 on t2.pmid = t1.pmid AND t1.topic != t2.topic
    WHERE t1.pub_date > (SELECT t2 FROM vars) AND t1.pub_date <= (SELECT t3 FROM vars)
    GROUP BY topic_1, topic_2
    HAVING cnt >= 5
)

--SELECT topic_1, topic_2, cnt FROM pairs_b_counts ORDER BY cnt DESC;

-- sum of all pair counts
, pairs_b_sum AS (
    SELECT SUM(cnt)/2 as sum
    FROM pairs_b_counts
)

-- total uniqe pairs
, pairs_b_unique AS (
    SELECT COUNT(*)/2 as pairs
    FROM pairs_b_counts
)

-- put it in one table
, pairs_b AS (
    SELECT 
        topic_1, topic_2, 
        cnt::DECIMAL, sum::DECIMAL, pairs
    FROM pairs_b_counts 
    CROSS JOIN pairs_b_sum
    CROSS JOIN pairs_b_unique
)


-- Topics from time range A

-- counts for each topic
, topics_a_counts AS (
    SELECT DISTINCT
        t.topic as topic,
        COUNT(*) as cnt
    FROM topics t
    WHERE pub_date > (SELECT t1 FROM vars) AND pub_date <= (SELECT t2 FROM vars)
    GROUP BY topic
    HAVING cnt >= 5
)

-- sum of all topic counts
, topics_a_sum AS (
    SELECT SUM(cnt) as sum FROM topics_a_counts
)

-- put it in one table
, topics_a AS (
    SELECT topic, cnt, sum
    FROM topics_a_counts CROSS JOIN topics_a_sum
)

--SELECT * FROM topics_a;


-- Topics from time range B

-- counts for each topic
, topics_b_counts AS (
    SELECT DISTINCT
        t.topic as topic,
        COUNT(*) as cnt
    FROM topics t
    WHERE pub_date > (SELECT t2 FROM vars) AND pub_date <= (SELECT t3 FROM vars)
    GROUP BY topic
    HAVING cnt >= 5
)

-- sum of all topic counts
, topics_b_sum AS (
    SELECT SUM(cnt) as sum FROM topics_b_counts
)

-- count of distinct pairs this topic appears in
, topics_b_pair_counts AS (
    SELECT 
        topic_1 AS topic, 
        COUNT(*) as pairs
    FROM pairs_b
    GROUP BY topic_1
)

--SELECT * FROM topics_b_pair_counts;

--put it in one table
, topics_b AS (
    SELECT tc.topic, cnt, pairs, sum
    FROM topics_b_counts tc
    JOIN topics_b_pair_counts pc ON tc.topic = pc.topic
    CROSS JOIN topics_b_sum
)


-- all mesh topic definitions
, topic_defs AS (
    SELECT
        ANY_VALUE(c.STR) as topic,
        ANY_VALUE(d.DEF) as def,
        CASE WHEN ANY_VALUE(h.ptr) LIKE 'A0434168.A2367943.A18456972.A0135348%' THEN 'Social Phenomena'
            WHEN ANY_VALUE(h.ptr) LIKE 'A0434168.A2367943.A18456972.A0135434%' THEN 'Health Care'
            WHEN ANY_VALUE(h.ptr) LIKE 'A0434168.A2367943.A18456972.A0135482%' THEN 'Psychiatry and Psychology'
            WHEN ANY_VALUE(h.ptr) LIKE 'A0434168.A2367943.A18456972.A0135391%' THEN 'Diseases'
            WHEN ANY_VALUE(h.ptr) LIKE 'A0434168.A2367943.A18456972.A0135345%' THEN 'Techniques and Equipment'
            WHEN ANY_VALUE(h.ptr) LIKE 'A0434168.A2367943.A18456972.A0135346%' THEN 'Anatomy'
            WHEN ANY_VALUE(h.ptr) LIKE 'A0434168.A2367943.A18456972.A0135374%' THEN 'Chemicals and Drugs'
            WHEN ANY_VALUE(h.ptr) LIKE 'A0434168.A2367943.A18456972.A0723397%' THEN 'Information Science'
            WHEN ANY_VALUE(h.ptr) LIKE 'A0434168.A2367943.A18456972.A0135443%' THEN 'Humanities'
            WHEN ANY_VALUE(h.ptr) LIKE 'A0434168.A2367943.A18456972.A18450781%' THEN 'Phenomena and Processes'
            WHEN ANY_VALUE(h.ptr) LIKE 'A0434168.A2367943.A18456972.A12093488%' THEN 'Human Groups'
            WHEN ANY_VALUE(h.ptr) LIKE 'A0434168.A2367943.A18456972.A18460084%' THEN 'Disciplines and Occupations'
            WHEN ANY_VALUE(h.ptr) LIKE 'A0434168.A2367943.A18456972.A0135472%' THEN 'Organisms'
            WHEN ANY_VALUE(h.ptr) LIKE 'A0434168.A2367943.A18456972.A12067976%' THEN 'Technology, Industry, and Agriculture'
            WHEN ANY_VALUE(h.ptr) LIKE 'A0434168.A2367943.A12078954%' THEN 'Geographicals'
            ELSE 'Other' END AS category
    FROM concept_map c
    LEFT JOIN definitions d ON c.AUI = d.AUI
    JOIN MRHIER h ON h.cui = c.cui AND h.aui = c.aui
    WHERE c.SAB = 'MSH'
    GROUP BY CODE
)


-- Put it all together to create topic co-occurence table

, totals AS (
    SELECT 
        pa.topic_1 as topic_1,
        pa.topic_2 as topic_2,
        tb1.cnt as total_1,  -- occurences of this topic
        tb2.cnt as total_2,
        d1.def as def_1,
        d2.def as def_2,
        d1.category as cat_1,
        d2.category as cat_2,
        PERCENT_RANK() OVER (ORDER BY tb1.cnt) as perc_1,
        PERCENT_RANK() OVER (ORDER BY tb2.cnt) as perc_2,

        --tb1.cnt/tb1.sum as topic1_over_tot_topics,
        --tb2.cnt/tb1.sum as topics2_over_tot_topics,
        pb.cnt + pa.cnt AS total,  -- total occurrences
        PERCENT_RANK() OVER (ORDER BY total) AS total_percentile,
        ((pb.cnt+pa.cnt)/(pb.sum+pa.sum))::DECIMAL(10,9) AS frequency,  -- total frequency
        PERCENT_RANK() OVER (ORDER BY frequency) as frequency_percentile,
        (pb.cnt/pb.sum)::DECIMAL(10,9) AS b_freq,
        (pa.cnt/pa.sum)::DECIMAL(10,9) AS a_freq,
        (b_freq - a_freq)/(a_freq) as "delta",
        --PERCENT_RANK() OVER (ORDER BY "delta") as delta_percentile,

        --tb1.pairs as topic1_pairs,
        --tb2.pairs as topic2_pairs,

        --tb1.pairs/pb.pairs as topic_1_pair_frac,
        --tb2.pairs/pb.pairs as topic_2_pair_frac,

        -- inverse proportion of unique pairs associated with each topic. If there are a lot of different things these topics are related to, it's less relevant.
        (pb.pairs::DECIMAL/(tb1.pairs::DECIMAL+tb2.pairs::DECIMAL)::DECIMAL) as relevance,
        --pb.pairs/tb1.pairs as topic_1_relevance,
        --pb.pairs/tb2.pairs as topic_2_relevance,

        -- conditional probabilites for each topic
        pb.cnt/tb1.cnt as prob_1,
        pb.cnt/tb2.cnt as prob_2


    FROM pairs_a pa
    JOIN pairs_b pb ON pa.topic_1 = pb.topic_1 and pa.topic_2 = pb.topic_2
    JOIN topics_b tb1 ON pa.topic_1 = tb1.topic
    JOIN topics_b tb2 ON pa.topic_2 = tb2.topic
    LEFT JOIN topic_defs d1 ON pb.topic_1 = d1.topic
    LEFT JOIN topic_defs d2 ON pb.topic_2 = d2.topic
    WHERE cat_1 IS NOT NULL and cat_2 IS NOT NULL
    ORDER BY frequency DESC
)

-- negative delta stats
, delta_perc AS (
    SELECT topic_1, topic_2, PERCENT_RANK() OVER (ORDER BY "delta" DESC) as delta_percentile
        FROM totals
        WHERE "delta" < 0
    UNION ALL
    SELECT topic_1, topic_2, PERCENT_RANK() OVER (ORDER BY "delta") AS delta_percentile
        FROM totals
        WHERE "delta" >= 0
)

-- factors for normalizing deltas (single values)
, norm_factors AS (
    SELECT MIN("delta") as min_delta, MAX("delta") as max_delta
    FROM totals
) 

-- stats for each topic
, stats AS (
    SELECT 
        topic_1 as topic,
        AVG(prob_1) as prob
    FROM totals
    GROUP BY topic_1
)


, results AS (
    SELECT 
        t.*,
        d.delta_percentile,
        d.delta_percentile * t.frequency_percentile AS importance,
        PERCENT_RANK() OVER (ORDER BY ABS(t."delta")) as delta_abs_percentile,  -- percentile of the absolute value of the delta
        PERCENT_RANK() OVER (ORDER BY importance) as importance_percentile,
        s1.prob * s2.prob as avg_prob 
    FROM totals t
    JOIN stats s1 ON s1.topic = t.topic_1
    JOIN stats s2 ON s2.topic = t.topic_2
    JOIN delta_perc d ON d.topic_1 = t.topic_1 AND d.topic_2 = t.topic_2
    CROSS JOIN norm_factors nf
)

SELECT * FROM results ORDER BY topic_1, topic_2
        """)

        return ["topic_co_occurrence_graph"]

    def citation_graph(self):
        """ Table to query for the citation graph """
        self.log("Creating Citation Graph table...")
        self.db.query("DROP TABLE IF EXISTS citation_graph")
        self.db.query(f"""
CREATE TABLE citation_graph AS
WITH

c AS (
    SELECT 
        c.pmid,
        c.citedby,
        c.citation_date,
        ROW_NUMBER() OVER (PARTITION BY c.pmid ORDER BY s.relative_citation_ratio DESC NULLS LAST) as num -- order by "importance"
    FROM citations c
    JOIN citation_stats s ON c.citedby = s.pmid
    WHERE c.citation_date IS NOT NULL
)

SELECT * FROM c WHERE num <= 3;  -- take only the 3 most "important" citations
""")
        return ["citation_graph"]

    def triple_graph(self):

        """ Table to query for the triple graph """
        self.log("Creating Triple Graph Tables...")

        # regular triple graph
        query = f"""
CREATE TABLE triple_graph AS
WITH
formatted_affiliations AS (
	SELECT 
		a.pmid,
		LISTAGG(DISTINCT a.first_name || ' ' || a.last_name, ';') WITHIN GROUP (ORDER BY a.affiliation_num ASC) as authors
	FROM affiliations a
	GROUP BY a.pmid
),

results AS (
	SELECT
    	ANY_VALUE(t.pmid) as pmid,
        ANY_VALUE(t.triple_id) as triple_id,
        t.subject,
		t.relation,
		t.object,
		LISTAGG(DISTINCT cs.concept_id, ';') WITHIN GROUP (ORDER BY cs.concept_id ASC) as subject_umls_topics,
		LISTAGG(DISTINCT co.concept_id, ';') WITHIN GROUP (ORDER BY cs.concept_id ASC) as object_umls_topics,
		LISTAGG(DISTINCT cr.concept_id, ';') WITHIN GROUP (ORDER BY cs.concept_id ASC) as relation_umls_topics,
        ANY_VALUE(cs.total_concepts) as cs_total_concepts,
        ANY_VALUE(co.total_concepts) as co_total_concepts,
		ANY_VALUE(t.start_char) as start_char,
		ANY_VALUE(t.end_char) as end_char,
		ANY_VALUE(t.confidence) as confidence,
		ANY_VALUE(c.citation_count) as citations,
		ANY_VALUE(t.pub_date) as pub_date,
		ANY_VALUE(p.pub_title) as pub_title,
		ANY_VALUE(p.journal_title) as journal_title,
		ANY_VALUE(id.doi) as doi,
		ANY_VALUE(a.authors) as authors,
		ANY_VALUE(d.content) as abstract,
		ANY_VALUE(l.project_number) as core_project_number
	FROM triples t
	JOIN formatted_affiliations a ON t.pmid = a.pmid
	LEFT JOIN citation_stats c ON t.pmid = c.pmid
    LEFT JOIN publications p ON t.pmid = p.pmid
	LEFT JOIN link_tables l ON t.pmid = l.pmid
	JOIN concepts cs ON cs.pmid = t.pmid AND cs.triple_id = t.triple_id AND cs.concept_type = 'subject' AND cs.concept_name IS NOT NULL
	JOIN concepts co ON co.pmid = t.pmid AND co.triple_id = t.triple_id AND co.concept_type = 'object' AND co.concept_name IS NOT NULL
	JOIN concepts cr ON cr.pmid = t.pmid AND cr.triple_id = t.triple_id AND cr.concept_type = 'relation' AND cr.concept_name IS NOT NULL
	JOIN documents d ON d.pmid = t.pmid AND d.content_type = 'abstract'
	JOIN id_map id ON id.pmid = t.pmid
	AND t.pub_date IS NOT NULL
	GROUP BY subject, relation, object
    HAVING cs_total_concepts > 1 AND co_total_concepts > 1
)

SELECT * FROM results
ORDER BY confidence DESC, (cs_total_concepts + co_total_concepts) DESC, citations DESC
"""
        self.db.query("DROP TABLE IF EXISTS triple_graph")
        self.db.query(query)

        # triples table with filtered relations
        self.db.query("DROP TABLE IF EXISTS triples_filtered_relations")
        self.db.query("DROP TABLE IF EXISTS triples_filtered_relations_concepts")
        self.db.query("""
CREATE TABLE triples_filtered_relations AS 
SELECT t.pmid, t.triple_id, t.pub_date, t.subject, t.relation, t.object, t.confidence, t.sentence_number, t.start_char, t.end_char
FROM concepts c
JOIN triples t ON t.pmid = c.pmid AND t.triple_id = c.triple_id
JOIN concepts cs ON t.pmid = cs.pmid AND t.triple_id = cs.triple_id AND cs.concept_type = 'subject' AND cs.total_concepts = 2
JOIN concepts co ON t.pmid = co.pmid AND t.triple_id = co.triple_id AND co.concept_type = 'object' AND co.total_concepts = 2
WHERE c.concept_type = 'relation' AND c.concept_name IN ('Associated with', 'Increased', 'Increase','Increasing','Activation action','Affecting','Positive', 'Negative','Decreased','Decrease','Improved','Reduced','Influence','Induce (action)','Enhance (action)','Changing','Correlation','Effect','Promotion (action)','Affecting','Suppressed','Risk','inhibited','Regulation', 'PREVENT (product)',
'Modulated',
'Affecting',
'Treating',
'Predictor',
'Removed',
'Incresing',
'Benefit',
'Decrease',
'Impaired',
'Improvement',
'Inhibition',
'Improving (qualifier value)',
'Decreasing',
'Determined by',
'Triggered by'
)
GROUP BY t.pmid, t.triple_id, t.pub_date, t.subject, t.relation, t.object, t.confidence, t.sentence_number, t.start_char, t.end_char;

""")
        self.db.query("""
CREATE TABLE triples_filtered_relations_concepts AS 
SELECT c.*
FROM triples_filtered_relations t
JOIN concepts c ON t.pmid = c.pmid AND c.triple_id = t.triple_id;
""")

        # filtered triple graph
        query = f"""
        CREATE TABLE triple_graph_filtered_relations AS
        WITH
        formatted_affiliations AS (
        	SELECT 
        		a.pmid,
        		LISTAGG(DISTINCT a.first_name || ' ' || a.last_name, ';') WITHIN GROUP (ORDER BY a.affiliation_num ASC) as authors
        	FROM affiliations a
        	GROUP BY a.pmid
        ),

        results AS (
        	SELECT
            	ANY_VALUE(t.pmid) as pmid,
                ANY_VALUE(t.triple_id) as triple_id,
                t.subject,
        		t.relation,
        		t.object,
        		LISTAGG(DISTINCT cs.concept_id, ';') WITHIN GROUP (ORDER BY cs.concept_id ASC) as subject_umls_topics,
        		LISTAGG(DISTINCT co.concept_id, ';') WITHIN GROUP (ORDER BY cs.concept_id ASC) as object_umls_topics,
        		LISTAGG(DISTINCT cr.concept_id, ';') WITHIN GROUP (ORDER BY cs.concept_id ASC) as relation_umls_topics,
                ANY_VALUE(cs.total_concepts) as cs_total_concepts,
                ANY_VALUE(co.total_concepts) as co_total_concepts,
        		ANY_VALUE(t.start_char) as start_char,
        		ANY_VALUE(t.end_char) as end_char,
        		ANY_VALUE(t.confidence) as confidence,
        		ANY_VALUE(c.citation_count) as citations,
        		ANY_VALUE(t.pub_date) as pub_date,
        		ANY_VALUE(p.pub_title) as pub_title,
        		ANY_VALUE(p.journal_title) as journal_title,
        		ANY_VALUE(id.doi) as doi,
        		ANY_VALUE(a.authors) as authors,
        		ANY_VALUE(d.content) as abstract,
        		ANY_VALUE(l.project_number) as core_project_number
        	FROM triples_filtered_relations t
        	JOIN formatted_affiliations a ON t.pmid = a.pmid
        	LEFT JOIN citation_stats c ON t.pmid = c.pmid
            LEFT JOIN publications p ON t.pmid = p.pmid
        	LEFT JOIN link_tables l ON t.pmid = l.pmid
        	JOIN triples_filtered_relations_concepts cs ON cs.pmid = t.pmid AND cs.triple_id = t.triple_id AND cs.concept_type = 'subject' AND cs.concept_name IS NOT NULL
        	JOIN triples_filtered_relations_concepts co ON co.pmid = t.pmid AND co.triple_id = t.triple_id AND co.concept_type = 'object' AND co.concept_name IS NOT NULL
        	JOIN triples_filtered_relations_concepts cr ON cr.pmid = t.pmid AND cr.triple_id = t.triple_id AND cr.concept_type = 'relation' AND cr.concept_name IS NOT NULL
        	JOIN documents d ON d.pmid = t.pmid AND d.content_type = 'abstract'
        	JOIN id_map id ON id.pmid = t.pmid
        	AND t.pub_date IS NOT NULL
        	GROUP BY subject, relation, object
            HAVING cs_total_concepts > 1 AND co_total_concepts > 1
        )

        SELECT * FROM results
        ORDER BY confidence DESC, (cs_total_concepts + co_total_concepts) DESC, citations DESC
        """
        self.db.query("DROP TABLE IF EXISTS triple_graph_filtered_relations")
        self.db.query(query)


        return ["triple_graph", "triple_graph_filtered_relations", "triples_filtered_relations", "triples_filtered_relations_concepts"]

    def autocomplete_tables(self):
        """
        Create pre-computed static tables.
        Must occur AFTER information extraction and all other pre-computed tables are created.
        """
        # UMLS Concept Autocomplete
        self.log("Creating UMLS Concept Autocomplete Table...")
        self.db.query("DROP TABLE IF EXISTS umls_concept_autocomplete")
        self.db.query("""
        CREATE TABLE umls_concept_autocomplete AS
        WITH counts AS (
            SELECT concept_name, COUNT(concept_name) cnt FROM concepts
            WHERE (concept_type = 'subject' OR concept_type = 'object')
            AND concept_name NOT LIKE '%-%-%' AND concept_name NOT LIKE '% % % %'  -- don't have 2+ hyphens or 3+ spaces
            GROUP BY concept_name
            ORDER BY cnt DESC
            LIMIT 10000
        )
        SELECT * FROM counts ORDER BY lower(concept_name)
        """)

        # MESH Topic Autocomplete
        self.log("Creating MESH Topic Autocomplete Table...")
        self.db.query("DROP TABLE IF EXISTS mesh_topic_autocomplete")
        self.db.query("""
        CREATE TABLE mesh_topic_autocomplete AS
        WITH

        counts AS (
            SELECT topic_1 as concept_name, ANY_VALUE(total_1) as cnt
            FROM topic_co_occurrence_graph t
            GROUP BY topic_1
            ORDER BY cnt DESC
            LIMIT 10000
        )
        SELECT * FROM counts ORDER BY lower(concept_name);
        """)
        return ['umls_concept_autocomplete', 'mesh_topic_autocomplete']