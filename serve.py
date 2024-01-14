from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask import render_template
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///papers.db'
db = SQLAlchemy(app)

class ResearchPaper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    authors = db.Column(db.String(500), nullable=False)
    abstract = db.Column(db.Text, nullable=False)
    arxiv_upload_date = db.Column(db.DateTime, nullable=True)
    arxiv_category = db.Column(db.String(100), nullable=True)
    arxiv_url = db.Column(db.String(500), nullable=True)
    publication_name = db.Column(db.String(250), nullable=True)
    publication_date = db.Column(db.DateTime, nullable=True)
    publication_url = db.Column(db.String(500), nullable=True)
    feature_vector = db.Column(db.PickleType, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
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

def compute_tfidf_vectors():
    papers = ResearchPaper.query.all()
    abstracts = [paper.abstract for paper in papers]

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(abstracts)

    for i, paper in enumerate(papers):
        paper.feature_vector = tfidf_matrix[i].toarray().tolist()
        db.session.commit()

@app.route('/compute_tfidf', methods=['GET'])
def compute_tfidf_endpoint():
    compute_tfidf_vectors()
    return jsonify({'message': 'TF-IDF vectors computed and stored.'})

@app.route('/search', methods=['POST'])
def search_papers():
    query = request.json['query']
    vectorizer = TfidfVectorizer()
    query_vector = vectorizer.transform([query]).toarray()

    # Dummy search implementation - Replace with actual search logic using TF-IDF vectors
    papers = ResearchPaper.query.all()
    search_results = [paper.to_dict() for paper in papers if query.lower() in paper.abstract.lower()]

    return jsonify(search_results)

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    papers = ResearchPaper.query.order_by(ResearchPaper.arxiv_upload_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('index.html', papers=papers.items, total_pages=papers.pages, current_page=page)


# @app.route('/get_papers', methods=['GET'])
# def get_papers():
#     page = request.args.get('page', 1, type=int)
#     per_page = request.args.get('per_page', 10, type=int)
#     papers = ResearchPaper.query.order_by(ResearchPaper.arxiv_upload_date.desc()).paginate(page, per_page, error_out=False)
#     papers_json = [paper.to_dict() for paper in papers.items]
#     return jsonify({'papers': papers_json, 'total': papers.total, 'pages': papers.pages, 'current_page': papers.page})

def setup_database(app):
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    setup_database(app)
    app.run(debug=True)