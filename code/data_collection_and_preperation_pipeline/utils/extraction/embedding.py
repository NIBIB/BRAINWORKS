from transformers import AutoTokenizer, AutoModel
import torch
import math

from utils.base import Base
from utils import MySQLDatabase
db = MySQLDatabase()


class EmbeddingModel(Base):
    def __init__(self, model):
        super().__init__()
        self.model_name = model
        self.tokenizer = AutoTokenizer.from_pretrained(model)
        self.model = AutoModel.from_pretrained(model, output_hidden_states=True)

        self.max = self.tokenizer.model_max_length  # max number of tokens that can be embedded at a time

        # global embedding matrix
        self.embedding = self.model.get_input_embeddings()

        # map dimension size to an embedding of that dimension
        self.embeddings = {
            2: self.reduce(2),
            self.embedding.embedding_dim: self.embedding
        }

        # if you change this, check the populate_database() function too
        self.columns = ['CUI', 'AUI', '2a', '2b', '3a', '3b', '3c', '5a', '5b', '5c', '5d', '5e']
        self.quote = ['CUI', 'AUI']
        self.table_name = "concept_embeddings"

    def reduce(self, n):
        """ Reduce the embedding matrix to n dimensions """
        self.mark_time("reduce")

        state = self.embedding.weight  # get the actual embedding matrix
        _, _, V = torch.pca_lowrank(state, q=n)  # returns U, S, V
        reduced = torch.matmul(state, V)
        # create new Torch Module of the same class type
        module = self.embedding.__class__(num_embeddings=self.embedding.num_embeddings, embedding_dim=n)
        module.load_state_dict({'weight': reduced})  # load the new reduced embedding matrix

        self.add_time("reduce")
        self.debug("PCA Time: ", self.get_time_total("reduce"))
        return module

    def get_vectors(self, words: list, n: int = None):
        """
        Return the n-dimensional embedding of each token
        If n is less than 0 or greater than the current embedding dimensions, return max dimensions
        """
        if 0 <= n >= self.embedding.embedding_dim: n = self.embedding.embedding_dim

        embedding = self.embeddings.get(n)
        if not embedding:  # this embedding dimension doesn't exist
            self.embeddings[n] = self.reduce(n)  # make it
            embedding = self.embeddings.get(n)

        vectors = []  # list of tuples (word, [vector])

        # split the word list into batches
        for i in range(0, len(words), self.max):
            batch = words[i:i+self.max]  # slice input to get batch
            encoded = self.tokenizer(batch, is_split_into_words=True, return_tensors="pt", add_special_tokens=False)  # returns a Tensor of token ids
            output = embedding(encoded.input_ids)
            output = output.squeeze(0)  # don't want the 0th dimension
            vectors += self.map_words_to_vectors(encoded, output)  # add to list of tuples

        return vectors

    def map_words_to_vectors(self, encoded, matrix):
        """
        Given a tokenizer output (encoded),
        and a corresponding <matrix> (from a model output),
        return a map of tuples that map words to their corresponding vector (as a list).
        """
        words = []  # map words to a list of their token vector indexes
        last_word_id = None
        for word_id in encoded.word_ids():  # indexes of words in the original sentence
            if word_id is None: continue
            if last_word_id == word_id: continue  # skip if it's the same word
            last_word_id = word_id

            start, end = encoded.word_to_tokens(word_id)  # start and end index of token IDs
            ids = list(encoded['input_ids'][0][start:end])  # list of token IDs for this work
            word = self.tokenizer.decode(ids)  # original word associated with these tokens
            words.append((word, [i for i in range(start, end)]))

        vectors = []  # map words to their vector
        for word, indexes in words:
            tensor = torch.stack([matrix[i] for i in indexes]).mean(dim=0)  # average all token vectors
            if tensor.size():  # has a length
                vectors.append((word, tensor.tolist()))
            else:  # it's a single scalar
                vectors.append((word, [tensor.tolist()]))  # need to put it in a list because .tolist() doesn't do it's job https://github.com/pytorch/pytorch/issues/52262
        return vectors

    # Database stuff
    def populate_database(self, replace=False, batch_size=10000):
        """ Populate the database table with coordinates """
        query = f"""CREATE TABLE IF NOT EXISTS `{self.table_name}` (
                  `{self.columns[0]}`   char(8)             NOT NULL     COMMENT 'The CUI of this concept',
                  `{self.columns[1]}`   varchar(9)          NOT NULL     COMMENT 'The AUI of this concept',
                  `{self.columns[2]}`   float               NOT NULL     COMMENT 'Coordinate A of the 2D embedding',
                  `{self.columns[3]}`   float               NOT NULL     COMMENT 'Coordinate B of the 2D embedding',
                  `{self.columns[4]}`   float               NOT NULL     COMMENT 'Coordinate A of the 3D embedding',
                  `{self.columns[5]}`   float               NOT NULL     COMMENT 'Coordinate B of the 3D embedding',
                  `{self.columns[6]}`   float               NOT NULL     COMMENT 'Coordinate C of the 3D embedding',
                  `{self.columns[7]}`   float               NOT NULL     COMMENT 'Coordinate A of the 5D embedding',
                  `{self.columns[8]}`   float               NOT NULL     COMMENT 'Coordinate B of the 5D embedding',
                  `{self.columns[9]}`   float               NOT NULL     COMMENT 'Coordinate C of the 5D embedding',
                  `{self.columns[10]}`  float               NOT NULL     COMMENT 'Coordinate D of the 5D embedding',
                  `{self.columns[11]}`  float               NOT NULL     COMMENT 'Coordinate E of the 5D embedding',
                  PRIMARY KEY (`AUI`),
                  KEY          `CUI_index`         (`CUI`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
        db.query(query)

        # get all CUIs
        self.log("Retrieving concepts from database...")
        self.mark_time("query")
        if replace:  # get all concepts
            query = """SELECT DISTINCT CUI, AUI, STR FROM concept_map"""
        else:  # get all concepts not already in the embedding table
            query = f"""SELECT DISTINCT CUI, AUI, STR FROM concept_map WHERE (CUI, AUI) NOT IN (SELECT CUI, AUI FROM {self.table_name})"""
        rows = db.query(query)
        self.add_time("query")
        self.log(f"Total Query Time: {self.get_time_total('query')}")

        words = []
        cuis = []
        auis = []
        for row in rows:
            cuis.append(row['CUI'])
            auis.append(row['AUI'])
            words.append(row['STR'])

        self.log(f"Total words: {len(words):,}")
        self.log(f"Batch size: {batch_size:,}")
        batches = int(math.ceil(len(words) / batch_size))
        self.log(f"Total batches: {batches:,}")
        b = 0
        for i in range(0, len(words), batch_size):
            batch_words = words[i:i+batch_size]  # slice words to get the current batch
            batch_cuis = cuis[i:i+batch_size]
            batch_auis = auis[i:i+batch_size]

            self.mark_time('vec')  # time it

            v2d = self.get_vectors(batch_words, 2)
            v3d = self.get_vectors(batch_words, 3)
            v5d = self.get_vectors(batch_words, 5)

            self.add_time('vec')  # stop timing

            # construct rows to insert
            self.mark_time('parse')
            rows = []
            for j in range(len(batch_words)):  # for each word
                cui = batch_cuis[j]
                aui = batch_auis[j]

                # each element in the list of vectors is a tuple (word, [v1, v2, v3, ...])
                rows.append([
                    cui, aui,
                    v2d[j][1][0], v2d[j][1][1],
                    v3d[j][1][0], v3d[j][1][1], v3d[j][1][2],
                    v5d[j][1][0], v5d[j][1][1], v5d[j][1][2], v5d[j][1][3], v5d[j][1][4]
                ])
            self.add_time('parse')

            self.mark_time("insert")
            self.insert(rows)
            self.add_time("insert")

            progress = self.progress(b, batches, every=1)
            if progress:
                total = self.get_time_total('vec',0)
                vec = self.get_time_last('vec')
                parse = self.get_time_last('parse')
                insert = self.get_time_last('insert')
                self.log(f"{progress} | {total:<10} | {vec:<8} | {parse:<8} | {insert:<8}")
            b += 1

        self.log(f"Batch size: {batch_size}")
        self.log(f"Avg. Vector Time: {self.get_time_avg('vec')} | Total Vector Time: {self.get_time_sum('vec')}")
        self.log(f"Avg. Parse Time: {self.get_time_avg('parse')} | Total Parse Time: {self.get_time_sum('parse')}")
        self.log(f"Avg. Insert Time: {self.get_time_avg('insert')} | Total Insert Time: {self.get_time_sum('insert')}")

    def insert(self, rows):
        """
        Insert rows into the database.
        <rows> should be a list of lists of items for their respective column.
        """
        assert len(rows[0]) == len(self.columns), "Length of rows to insert do not match length of columns."
        # construct values in this row for the INSERT statement
        row_values = []
        for row in rows:
            _row = []
            for i, item in enumerate(row):
                if item is None:
                    item = "NULL"
                elif self.columns[i] in self.quote:
                    item = f"'{str(item)}'"
                else:
                    item = str(item)
                _row.append(item)
            row_values.append(f"({', '.join(_row)})")

        query = f"""
        INSERT IGNORE `{self.table_name}` ({', '.join(self.columns)})
        VALUES {', '.join(row_values)}
        """
        db.query(query)


def get_stats(models):
    """ Get vocab statistics from the database """
    query = """SELECT DISTINCT STR FROM concept_map"""
    print("Compiling umls words...")
    umls_words = db.query(query)
    umls_words = set([r['STR'] for r in umls_words])
    umls_total = len(umls_words)

    query = """SELECT DISTINCT STR FROM concepts JOIN concept_map ON concepts.concept_id = concept_map.CUI"""
    print("Compiling extracted words...")
    extracted_words = db.query(query)
    extracted_words = set([r['STR'] for r in extracted_words])
    extracted_total = len(extracted_words)

    print(f"Total UMLS: ", umls_total)
    print(f"Total Extracted: ", extracted_total)

    for name in models:
        model = EmbeddingModel(name)
        vocab = model.tokenizer.get_vocab()  # get vocab dictionary
        print()
        print("Model: ", name)
        print(f"Total Vocab: ", len(vocab))

        umls_covered = 0  # number of words in the model
        extracted_covered = 0  # number of words in the model
        for word in vocab.keys():
            if word in umls_words: umls_covered += 1
            if word in extracted_words: extracted_covered += 1

        print(f"UMLS Coverage: {round((umls_covered / umls_total) * 100, 2)}%  ({umls_covered})")
        print(f"Extracted Coverage: {round((extracted_covered/extracted_total)*100,2)}%  ({extracted_covered})")