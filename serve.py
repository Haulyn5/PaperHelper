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

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///papers.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)


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

@app.route('/add_paper', methods=['POST'])
def add_paper():
    data = request.json
    new_paper = ResearchPaper(
        title=data['title'],
        authors=data['authors'],
        abstract=data['abstract'],
        arxiv_upload_date=data.get('arxiv_upload_date'),
        arxiv_category=data.get('arxiv_category'),
        arxiv_url=data.get('arxiv_url'),
        publication_name=data.get('publication_name'),
        publication_date=data.get('publication_date'),
        publication_url=data.get('publication_url')
    )
    db.session.add(new_paper)
    db.session.commit()
    return jsonify({'message': 'Paper added successfully', 'paper_id': new_paper.id}), 201

@app.route('/get_paper/<int:paper_id>', methods=['GET'])
def get_paper(paper_id):
    paper = ResearchPaper.query.get_or_404(paper_id)
    return jsonify(paper.to_dict())

# For TF-IDF vectors
def load_vectorizer():
    try:
        with open('tfidf_vectorizer.pkl', 'rb') as file:
            return pickle.load(file)
    except FileNotFoundError:
        flash("Vectorizer file not found. Please run 'compute_feature.py' to generate search vectors.", "error")
        return None

# load tfidf vectors
def load_feature_vectors():
    if os.path.exists('feature_vectors.npz'):
        return sparse.load_npz('feature_vectors.npz')
    return None

def load_semantic_vectors():
    if os.path.exists('semantic_vectors.npz'):
        return np.load('semantic_vectors.npz', allow_pickle=True)['vectors'].item()
    return None


def search_papers(query, vectorizer):
    # papers = ResearchPaper.query.all()
    # feature_matrix = load_feature_vectors()
    # query_vector = vectorizer.transform([query])
    # # print(f"Query vector shape: {query_vector.shape}")

    # if feature_matrix is not None:
    #     similarities = cosine_similarity(feature_matrix, query_vector).flatten()
    #     paper_scores = [(papers[i], similarities[i]) for i in range(len(papers)) if similarities[i] > 0]
    #     sorted_papers = sorted(paper_scores, key=lambda x: x[1], reverse=True)
    #     return sorted_papers
    # return []
    start_time = time.time()
    semantic_vectors = load_semantic_vectors()
    if not semantic_vectors:
        flash("Semantic vectors not found. Please run 'compute_feature.py' to generate them.", "error")
        return []
    print(f"Time for loading semantic vectors: {time.time() - start_time} seconds.")
    start_time = time.time()
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L12-v2')
    query_vector = model.encode([query])
    print(f"Time for encoding query: {time.time() - start_time} seconds.")
    start_time = time.time()
    # Convert semantic vectors to a matrix
    paper_ids = list(semantic_vectors.keys())
    vectors_matrix = np.array([semantic_vectors[pid] for pid in paper_ids])
    print(f"Time for converting semantic vectors to a matrix: {time.time() - start_time} seconds.")
    start_time = time.time()
    # Compute similarities in bulk
    similarities = cosine_similarity(query_vector, vectors_matrix)[0]
    print(f"Time for computing similarities: {time.time() - start_time} seconds.")
    start_time = time.time()
    # Filter out papers with zero similarity
    relevant_papers = [(int(pid), sim) for pid, sim in zip(paper_ids, similarities) if sim > 0]
    # Fetch all relevant papers in one query
    relevant_paper_ids = [pid for pid, _ in relevant_papers]
    papers = ResearchPaper.query.filter(ResearchPaper.id.in_(relevant_paper_ids)).all()
    papers_dict = {paper.id: paper for paper in papers}

    # Create a sorted list of (paper, similarity) tuples
    paper_scores = sorted([(papers_dict[pid], sim) for pid, sim in relevant_papers], key=lambda x: x[1], reverse=True)
    print(f"Time for creating tuples: {time.time() - start_time} seconds.")
    return paper_scores

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


def find_similar_papers(paper_id, top_n=100):
    # feature_matrix = load_feature_vectors()
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
    similar = find_similar_papers(paper_id, top_n=20)
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


def setup_database(app):
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    setup_database(app)
    app.run(debug=True, port=40500)