import json
from flask import Flask, request, jsonify, render_template, flash, get_flashed_messages, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os
from scipy import sparse
from datetime import datetime
from sentence_transformers import SentenceTransformer
import time
from flask_caching import Cache

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///papers.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)
# cache
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
cache.init_app(app)
# Set a timeout for cache, e.g., 5 minutes
CACHE_TIMEOUT = 300
sentence_transformer_model = None

class ResearchPaper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    authors = db.Column(db.String(500), nullable=False)
    abstract = db.Column(db.Text, nullable=False)
    arxiv_id = db.Column(db.String(100), nullable=True)
    arxiv_upload_date = db.Column(db.DateTime, nullable=True)
    arxiv_category = db.Column(db.String(100), nullable=True)
    arxiv_url = db.Column(db.String(500), nullable=True)
    publication_name = db.Column(db.String(250), nullable=True)
    publication_date = db.Column(db.DateTime, nullable=True)
    publication_url = db.Column(db.String(500), nullable=True)
    

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'arxiv_id': self.arxiv_id,
            'arxiv_upload_date': self.arxiv_upload_date.isoformat() if self.arxiv_upload_date else None,
            'arxiv_category': self.arxiv_category,
            'arxiv_url': self.arxiv_url,
            'publication_name': self.publication_name,
            'publication_date': self.publication_date.isoformat() if self.publication_date else None,
            'publication_url': self.publication_url
        }

# db.create_all()
    
def get_sentence_transformer_model():
    global sentence_transformer_model
    if sentence_transformer_model is None:
        sentence_transformer_model = SentenceTransformer('sentence-transformers/all-MiniLM-L12-v2')
    return sentence_transformer_model

def read_settings():
    with open('settings.json', 'r') as file:
        return json.load(file)



# For TF-IDF vectors
def load_vectorizer():
    try:
        with open('tfidf_vectorizer.pkl', 'rb') as file:
            return pickle.load(file)
    except FileNotFoundError:
        flash("Vectorizer file not found. Please run 'compute_feature.py' to generate search vectors.", "error")
        return None

# load tfidf vectors
def load_tfidf_feature_vectors():
    if os.path.exists('tfidf_feature_vectors.npz'):
        return sparse.load_npz('tfidf_feature_vectors.npz')
    return None

def load_semantic_vectors():
    if os.path.exists('semantic_vectors.npz'):
        return np.load('semantic_vectors.npz', allow_pickle=True)['vectors'].item()
    return None

@cache.memoize(timeout=CACHE_TIMEOUT)
def search_papers(query, vectorizer):
    settings = read_settings()
    search_feature = settings['search_feature']
    weights = settings.get('feature_weights', {'tfidf': 1, 'semantic': 1, 'match': 1})

    papers = ResearchPaper.query.all()
    paper_dict = {paper.id: paper for paper in papers}

    # Initialize score dictionaries
    tfidf_scores, semantic_scores, match_scores = {}, {}, {}
    combined_scores = {}

    # Load TF-IDF feature vectors
    if search_feature in ['tf-idf', 'combination']:
        tfidf_feature_matrix = load_tfidf_feature_vectors()
        tfidf_query_vector = vectorizer.transform([query])
        tfidf_similarities = cosine_similarity(tfidf_feature_matrix, tfidf_query_vector).flatten()
        for i, score in enumerate(tfidf_similarities):
            if score > 0:
                tfidf_scores[papers[i].id] = score
        # get max score and norm score
        max_score = max(tfidf_scores.values())
        for pid in tfidf_scores:
            tfidf_scores[pid] /= max_score
            combined_scores[pid] = combined_scores.get(papers[i].id, 0) + tfidf_scores[pid] * weights['tfidf']

    # Load Semantic vectors
    if search_feature in ['semantic', 'combination']:
        semantic_vectors = load_semantic_vectors()
        model = get_sentence_transformer_model()
        query_vector = model.encode([query])
        paper_ids = list(semantic_vectors.keys())
        vectors_matrix = np.array([semantic_vectors[pid] for pid in paper_ids])
        semantic_similarities = cosine_similarity(query_vector, vectors_matrix)[0]
        for pid, score in zip(paper_ids, semantic_similarities):
            if score > 0:
                semantic_scores[int(pid)] = score
        # get max score and norm score
        max_score = max(semantic_scores.values())
        for pid in semantic_scores:
            semantic_scores[pid] /= max_score
            combined_scores[pid] = combined_scores.get(pid, 0) + semantic_scores[pid] * weights['semantic']

    # Match Feature Calculation
    if search_feature in ['match', 'combination']:
        query_words = query.lower().split()
        for paper in papers:
            score = 0
            title_words = paper.title.lower().split()
            authors_words = paper.authors.lower().split()
            abstract_words = paper.abstract.lower().split()

            for word in query_words:
                score += 20 if word in title_words else 0
                score += 10 if word in authors_words else 0
                score += abstract_words.count(word)

            match_scores[paper.id] = score
        # get max score and avg score to norm score
        max_score = max(match_scores.values())
        avg_score = sum(match_scores.values()) / len(match_scores)
        for pid in match_scores:
            match_scores[pid] = (match_scores[pid] - avg_score) / max_score
            combined_scores[pid] = combined_scores.get(pid, 0) + match_scores[pid] * weights['match']

    # Normalize Scores if in 'combination' mode
    if search_feature == 'combination':
        max_score = max(combined_scores.values())
        for pid in combined_scores:
            combined_scores[pid] /= max_score

    # Choose final scores based on selected feature
    final_scores = combined_scores if search_feature == 'combination' else match_scores if search_feature == 'match' else semantic_scores if search_feature == 'semantic' else tfidf_scores

    # Sort and return papers based on the final scores
    sorted_papers = sorted([(paper_dict[pid], score) for pid, score in final_scores.items()], key=lambda x: x[1], reverse=True)
    return sorted_papers


@app.route('/', methods=['GET', 'POST'])
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    query = request.args.get('query', None)
    papers_to_show = []
    total_pages = 0
    print(f"query={query}")

    if query:
        vectorizer = load_vectorizer()
        if vectorizer:
            sorted_papers = search_papers(query, vectorizer)
            papers_to_show = sorted_papers[(page - 1) * per_page: page * per_page]
            total_pages = int(np.ceil(len(sorted_papers) / per_page))
    else:
        papers_query = ResearchPaper.query.order_by(ResearchPaper.arxiv_upload_date.desc())
        papers_to_show = [(paper, None) for paper in papers_query.paginate(page=page, per_page=per_page, error_out=False).items]
        total_pages = papers_query.paginate(page=page, per_page=per_page, error_out=False).pages
    return render_template('index.html', papers=papers_to_show, total_pages=total_pages, current_page=page, query=query)


def find_similar_papers(paper_id, top_n=25):
    # feature_matrix = load_tfidf_feature_vectors()
    # papers = ResearchPaper.query.all()

    # if feature_matrix is None or len(papers) == 0:
    #     return []
    # try:
    #     target_index = [p.id for p in papers].index(paper_id)
    #     target_vector = feature_matrix[target_index]
    # except ValueError:
    #     # paper_id not found in the list of IDs
    #     print(f"Paper ID {paper_id} not found in the database.")
    #     return []

    # similarities = cosine_similarity(feature_matrix, target_vector).flatten()

    # # Sort and get top N indices, excluding the target paper itself
    # similar_indices = np.argsort(similarities)[::-1]
    # similar_indices = [idx for idx in similar_indices if papers[idx].id != paper_id][:top_n]

    # similar_papers = [(papers[idx], similarities[idx]) for idx in similar_indices]
    # print(similar_indices)
    # return similar_papers
    start_time = time.time()
    semantic_vectors = load_semantic_vectors()
    if not semantic_vectors or str(paper_id) not in semantic_vectors:
        flash(f"Semantic vector for paper ID {paper_id} not found.", "error")
        return []

    # Convert semantic vectors to a matrix
    paper_ids = list(semantic_vectors.keys())
    vectors_matrix = np.array([semantic_vectors[pid] for pid in paper_ids])

    target_vector = semantic_vectors[str(paper_id)]
    print(f"Time for loading semantic vectors: {time.time() - start_time} seconds.")
    start_time = time.time()
    # Compute similarities in bulk
    similarities = cosine_similarity([target_vector], vectors_matrix)[0]
    print(f"Time for computing similarities: {time.time() - start_time} seconds.")
    start_time = time.time()

    # Create a list of (paper_id, similarity) tuples, excluding the target paper
    paper_scores = [(int(pid), sim) for pid, sim in zip(paper_ids, similarities) if pid != str(paper_id)]
    print(f"Time for creating tuples: {time.time() - start_time} seconds.")
    start_time = time.time()
    # Sort by similarity and select top N
    similar_papers = sorted(paper_scores, key=lambda x: x[1], reverse=True)[:top_n]
    similar_papers = [(ResearchPaper.query.get(pid), sim) for pid, sim in similar_papers]
    print(f"Time for sorting and selecting top N: {time.time() - start_time} seconds.")

    return similar_papers

@app.route('/similar/<int:paper_id>', methods=['GET'])
def similar_papers(paper_id):
    base_paper = ResearchPaper.query.get_or_404(paper_id)
    settings = read_settings()
    number_of_similar_papers = settings['number_of_similar_papers']
    similar = find_similar_papers(paper_id, top_n=number_of_similar_papers)
    return render_template('similar_papers.html', base_paper=base_paper, similar_papers=similar)

@app.route('/edit_paper/<int:paper_id>', methods=['GET'])
def edit_paper(paper_id):
    paper = ResearchPaper.query.get_or_404(paper_id)
    print(f"Debug:\nPaper Title: {paper.title}\nPaper Abstract: {paper.abstract}")
    return render_template('paper_info_edit.html', paper=paper)

@app.route('/update_paper', methods=['POST'])
def update_paper():
    paper_id = request.form['id']
    paper = ResearchPaper.query.get_or_404(paper_id)

    # Update fields
    paper.title = request.form['title']
    paper.authors = request.form['authors']
    paper.abstract = request.form['abstract']
    paper.arxiv_id = request.form.get('arxiv_id')

    # Handle dates
    arxiv_upload_date = request.form.get('arxiv_upload_date')
    publication_date = request.form.get('publication_date')

    # Convert string dates to datetime objects
    if arxiv_upload_date and isinstance(arxiv_upload_date, str):
        paper.arxiv_upload_date = datetime.strptime(arxiv_upload_date, '%Y-%m-%d')
    else:
        paper.arxiv_upload_date = None

    if publication_date and isinstance(publication_date, str):
        paper.publication_date = datetime.strptime(publication_date, '%Y-%m-%d')
    else:
        paper.publication_date = None

    paper.arxiv_category = request.form.get('arxiv_category')
    paper.arxiv_url = request.form.get('arxiv_url')
    paper.publication_name = request.form.get('publication_name')
    paper.publication_url = request.form.get('publication_url')


    db.session.commit()
    flash('Paper updated successfully!')
    return redirect(url_for('similar_papers', paper_id=paper_id))

@app.route('/settings', methods=['GET'])
def settings():
    with open('settings.json', 'r') as file:
        settings = json.load(file)
    return render_template('settings.html', settings=settings)

@app.route('/update_settings', methods=['POST'])
def update_settings():
    settings = {
        "default_arxiv_query": request.form['default_arxiv_query'],
        "number_of_similar_papers": int(request.form['number_of_similar_papers']),
        "search_feature": request.form['search_feature'],
        "feature_weights": {
            "tfidf": int(request.form['tfidf_weight']),
            "semantic": int(request.form['semantic_weight']),
            "match": int(request.form['match_weight'])
        }
    }
    with open('settings.json', 'w') as file:
        json.dump(settings, file)
    flash('Settings updated successfully!')
    return redirect(url_for('settings'))

def create_default_settings():
    default_settings = {
        "default_arxiv_query": "cat:cs.CV+OR+cat:cs.LG+OR+cat:cs.CL+OR+cat:cs.AI+OR+cat:cs.CR+OR+cat:eess.AS&sortBy=lastUpdatedDate&sortOrder=descending",
        "number_of_similar_papers": 25,
        "search_feature": "combination",
        "feature_weights": {
            "tfidf": 1,
            "semantic": 1,
            "match": 1
        }
    }
    with open('settings.json', 'w') as file:
        json.dump(default_settings, file)

def check_settings_file():
    if not os.path.isfile('settings.json'):
        create_default_settings()


def setup_database(app):
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    check_settings_file()
    setup_database(app)
    app.run(debug=True, port=40500)