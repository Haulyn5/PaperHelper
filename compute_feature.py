import time
from sklearn.feature_extraction.text import TfidfVectorizer
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from serve import ResearchPaper, db  # Adjust the import as necessary
import pickle

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///papers.db'  # Update to match your configuration
db.init_app(app)

def combine_text(paper):
    """ Combine title, authors, and abstract into a single string. """
    return ' '.join([paper.title, paper.authors, paper.abstract])

def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
    """ Print iterations progress. """
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end="\r")
    if iteration == total: 
        print()

def compute_tfidf_vectors():
    with app.app_context():
        start_time = time.time()
        papers = ResearchPaper.query.all()
        texts = [combine_text(paper) for paper in papers]

        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(texts)

        for i, paper in enumerate(papers):
            paper.feature_vector = tfidf_matrix[i].toarray()[0]
            db.session.add(paper)
            print_progress_bar(i + 1, len(papers), prefix='Progress:', suffix='Complete', length=50)

        db.session.commit()
        end_time = time.time()
        print(f"Completed TF-IDF computation in {end_time - start_time:.2f} seconds")
        # Save the fitted vectorizer
        with open('tfidf_vectorizer.pkl', 'wb') as file:
            pickle.dump(vectorizer, file)

if __name__ == "__main__":
    compute_tfidf_vectors()
    print("TF-IDF feature vectors computed and stored.")
