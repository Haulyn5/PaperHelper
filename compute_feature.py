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

def combine_text(paper):
    """ Combine title, authors, and abstract into a single string. """
    return ' '.join([paper.title, paper.authors, paper.abstract])

def compute_tfidf_vectors():
    with app.app_context():
        start_time = time.time()
        papers = ResearchPaper.query.all()
        texts = [combine_text(paper) for paper in papers]
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(texts)
        print(f"TF-IDF vectors computed. The shape of the matrix is {tfidf_matrix.shape}.")
        print("The size of the tfidf_matrix variable is:",sys.getsizeof(tfidf_matrix), "bytes.")

        # Saving the sparse matrix instead of dense arrays
        sparse.save_npz('feature_vectors.npz', tfidf_matrix)

        # Save the fitted vectorizer
        with open('tfidf_vectorizer.pkl', 'wb') as file:
            pickle.dump(vectorizer, file)
        print(f"TF-IDF vectors computed and stored in {time.time() - start_time} seconds.")
        print(f"Feature vectors stored in 'feature_vectors.npz'. TF-IDF vectorizer stored in 'tfidf_vectorizer.pkl'.")

if __name__ == "__main__":
    compute_tfidf_vectors()
    print("TF-IDF feature vectors computed and stored.")