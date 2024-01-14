import feedparser
import argparse
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from serve import ResearchPaper, db  # Adjust the import as necessary

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///papers.db'  # Make sure this matches your main application's configuration
db.init_app(app)

ARXIV_API_URL = "http://export.arxiv.org/api/query?search_query="

def fetch_arxiv_papers(query, max_results):
    with app.app_context():
        url = f"{ARXIV_API_URL}{query}&max_results={max_results}"
        feed = feedparser.parse(url)

        total_fetched, new_papers, updated_papers, already_exists = 0, 0, 0, 0

        for entry in feed.entries:
            total_fetched += 1
            existing_paper = ResearchPaper.query.filter_by(arxiv_url=entry.id).first()
            upload_date = datetime.strptime(entry.published, '%Y-%m-%dT%H:%M:%SZ')

            if existing_paper:
                if existing_paper.arxiv_upload_date < upload_date:
                    # Update all fields if the paper has a newer upload date
                    existing_paper.title = entry.title
                    existing_paper.authors = ', '.join(author.name for author in entry.authors)
                    existing_paper.abstract = entry.summary
                    existing_paper.arxiv_upload_date = upload_date
                    updated_papers += 1
                else:
                    already_exists += 1
            else:
                new_paper = ResearchPaper(
                    title=entry.title,
                    authors=', '.join(author.name for author in entry.authors),
                    abstract=entry.summary,
                    arxiv_upload_date=upload_date,
                    arxiv_url=entry.id
                )
                db.session.add(new_paper)
                new_papers += 1
        
        db.session.commit()
        return total_fetched, new_papers, updated_papers, already_exists


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fetch papers from arXiv and store them in the database.')
    parser.add_argument('max_results', type=int, nargs='?', default=10, help='Number of papers to fetch')
    args = parser.parse_args()

    default_query = "cat:cs.CV+OR+cat:cs.LG+OR+cat:cs.CL+OR+cat:cs.AI+OR+cat:cs.CR+OR+cat:eess.AS"
    stats = fetch_arxiv_papers(query=default_query, max_results=args.max_results)
    
    print(f"Total papers fetched: {stats[0]}")
    print(f"New papers added: {stats[1]}")
    print(f"Papers updated: {stats[2]}")
    print(f"Papers already existing in the database: {stats[3]}")
