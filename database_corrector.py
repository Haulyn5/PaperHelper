from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from serve import ResearchPaper, db  # Adjust the import as necessary
import unicodedata

def normalize_authors(authors_str):
    normalized_authors = unicodedata.normalize('NFKD', authors_str)
    return ''.join([c for c in normalized_authors if not unicodedata.combining(c)])


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///papers.db"
db.init_app(app)

def correct_paper_titles():
    with app.app_context():
        papers = ResearchPaper.query.all()
        for paper in papers:
            if paper.title.endswith('.'):
                corrected_title = paper.title.rstrip('.')
                duplicate_paper = ResearchPaper.query.filter_by(title=corrected_title, authors=paper.authors).first()

                if duplicate_paper:
                    # Copy current entry's publication info to the existing entry and delete the current entry
                    update_publication_info(duplicate_paper, paper)
                    db.session.delete(paper)
                else:
                    # Update the current entry to remove the dot from the title
                    paper.title = corrected_title
                    db.session.add(paper)

        db.session.commit()

def update_publication_info(existing_paper, current_paper):
    existing_paper.publication_name = current_paper.publication_name
    existing_paper.publication_date = current_paper.publication_date
    existing_paper.publication_url = current_paper.publication_url
    db.session.add(existing_paper)

def find_duplicates():
    with app.app_context():
        papers = ResearchPaper.query.all()
        duplicates = {}
        
        for paper in papers:
            normalized_title = paper.title.strip().rstrip('.')
            normalized_authors = normalize_authors(paper.authors)
            key = (normalized_title, normalized_authors)

            if key in duplicates:
                duplicates[key].append(paper)
            else:
                duplicates[key] = [paper]

        return {k: v for k, v in duplicates.items() if len(v) > 1}
    
def merge_publication_info(primary_paper, duplicate):
    with app.app_context():
        if duplicate.publication_name and not primary_paper.publication_name:
            primary_paper.publication_name = duplicate.publication_name
            primary_paper.publication_date = duplicate.publication_date
            primary_paper.publication_url = duplicate.publication_url

def merge_duplicates(duplicates):
    with app.app_context():
        for _, papers in duplicates.items():
            primary_paper = papers[0]  # Keep the first paper

            for duplicate in papers[1:]:
                # Merge information from duplicate into primary_paper
                merge_publication_info(primary_paper, duplicate)
                # Delete the duplicate
                db.session.delete(duplicate)

            db.session.add(primary_paper)
        db.session.commit()



if __name__ == "__main__":
    duplicates = find_duplicates()
    merge_duplicates(duplicates)
    print("Duplicate papers merged and removed.")
