import json
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from serve import ResearchPaper, db  # Adjust the import as necessary
import tqdm

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///papers.db'  # Ensure this matches your configuration
db.init_app(app)

def load_data(filename):
    with open(filename, 'r') as file:
        return json.load(file)

def insert_papers(papers_data):
    with app.app_context():
        for paper_id, paper_info in tqdm.tqdm(papers_data.items()):
            # print(f"Processing arxiv-sanity-lite paper with ID {paper_id}")
            # print(f"Paper info: {paper_info}")
            # Check if paper already exists
            paper_id = paper_id.split('v')[0]  # paper_id may looks like "2311.12796v1"
            existing_paper = ResearchPaper.query.filter_by(arxiv_id=paper_id).first()
            if existing_paper is not None:
                print(f"Paper with ID {paper_id} already exists.")
                continue
            # Create a new paper instance
            new_paper = ResearchPaper(
                title=paper_info['title'],
                authors=paper_info['authors'],
                abstract=paper_info['abstract'],
                arxiv_upload_date=datetime.strptime(paper_info['arxiv_upload_date'], '%Y-%m-%dT%H:%M:%SZ'),
                arxiv_category=paper_info['arxiv_categories'],
                arxiv_url=f"https://arxiv.org/abs/{paper_id}",
                arxiv_id=paper_id
            )
            db.session.add(new_paper)

        db.session.commit()

if __name__ == "__main__":
    papers_data = load_data('papers_data.json')
    insert_papers(papers_data)
    print("Data migration complete.")
