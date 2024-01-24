import time
from sklearn.feature_extraction.text import TfidfVectorizer
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from serve import ResearchPaper, db
import numpy as np
import tqdm
from scipy import sparse
import pickle
import sys


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///papers.db'  # Update to match your configuration
db.init_app(app)

def combine_text_tfidf(paper):
    """ Combine title, authors, and abstract into a single string. """
    return ' '.join([paper.title, paper.authors, paper.abstract])

def conbine_text_semantic(paper):
    result = "Title: "+paper.title + " Authors: "+paper.authors + " Abstract: "+paper.abstract
    return result

def compute_tfidf_vectors():
    with app.app_context():
        start_time = time.time()
        papers = ResearchPaper.query.all()
        texts = [combine_text_tfidf(paper) for paper in papers]
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(texts)
        print(f"TF-IDF vectors computed. The shape of the matrix is {tfidf_matrix.shape}.")
        print("The size of the tfidf_matrix variable is:",sys.getsizeof(tfidf_matrix), "bytes.")

        # Saving the sparse matrix instead of dense arrays
        sparse.save_npz('tfidf_feature_vectors.npz', tfidf_matrix)

        # Save the fitted vectorizer
        with open('tfidf_vectorizer.pkl', 'wb') as file:
            pickle.dump(vectorizer, file)
        print(f"TF-IDF vectors computed and stored in {time.time() - start_time} seconds.")
        print(f"Feature vectors stored in 'tfidf_feature_vectors.npz'. TF-IDF vectorizer stored in 'tfidf_vectorizer.pkl'.")

# below is semantic feature part
import hashlib
import json
import os
from sentence_transformers import SentenceTransformer

def compute_hash(paper):
    hasher = hashlib.sha256()
    content = ' '.join([paper.title, paper.authors, paper.abstract]).encode()
    hasher.update(content)
    return hasher.hexdigest()

def load_hashes(filename='paper_hashes.json'):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    return {}

def save_hashes(hashes, filename='paper_hashes.json'):
    with open(filename, 'w') as file:
        json.dump(hashes, file)


def load_semantic_vectors(filename='semantic_vectors.npz'):
    if os.path.exists(filename):
        return np.load(filename, allow_pickle=True)['vectors'].item()
    return {}

def load_semantic_vectors(filename='semantic_vectors.npz'):
    if os.path.exists(filename):
        return np.load(filename, allow_pickle=True)['vectors'].item()
    return {}

def compute_semantic_vectors():
    with app.app_context():
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L12-v2')
        papers = ResearchPaper.query.all()
        hashes = load_hashes()
        semantic_vectors = load_semantic_vectors()

        for paper in tqdm.tqdm(papers):
            current_hash = compute_hash(paper)
            # Check if paper is modified or semantic vector doesn't exist
            if hashes.get(str(paper.id)) != current_hash or str(paper.id) not in semantic_vectors:
                text = conbine_text_semantic(paper)
                semantic_vectors[str(paper.id)] = model.encode([text])[0]
                hashes[str(paper.id)] = current_hash

        # Save updated hashes and semantic vectors
        save_hashes(hashes)
        np.savez_compressed('semantic_vectors.npz', vectors=semantic_vectors)


if __name__ == "__main__":
    compute_tfidf_vectors()
    print("TF-IDF feature vectors computed and stored.")
    compute_semantic_vectors()
    print("Semantic feature vectors computed and stored.")