import argparse
from datetime import datetime
import time
import bibtexparser
from dblp_fetcher import update_existing_paper
from serve import db, ResearchPaper # Assuming db is your database instance
import tqdm
from flask import Flask


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///papers.db"
db.init_app(app)

def process_authors(authors):
    # The input is the authors field from a BibTeX entry
    # first in bib, the first name and the last name is separated by a comma
    # we want to separate the first name and the last name with just a space
    # and we want to separate the authors with a comma
    # Besides, in bib, the family name is placed before the given name
    # we want to reverse the order of the names
    # first splice the authors with the "and" and the comma
    authors_list = authors.split(' and ')
    for i in range(len(authors_list)):
        author = authors_list[i]
        author_name_parts = author.split(', ')
        if len(author_name_parts) == 1:  # name with {Firstname Lastname} like {Isaac Newton}
            continue
        elif len(author_name_parts) == 2:  # name with {Lastname, Firstname} like {Newton, Isaac}
            author_name_parts.reverse()
            authors_list[i] = ' '.join(author_name_parts)
        elif len(author_name_parts) == 3:  # name with {Lastname, Suffix, Firstname} like {Newton, Jr., Isaac}
            author_name_parts = [author_name_parts[2], author_name_parts[0], author_name_parts[1]]
            authors_list[i] = ' '.join(author_name_parts)
    authors = ', '.join(authors_list)

    # sencond, in bib, there are some authors name with special characters
    # we want to remove these special characters
    authors = authors.replace('{', '')
    authors = authors.replace('}', '')
    # remove the "\" and the command after it
    authors = authors.replace('\\', '')
    authors = authors.replace("'", '')
    authors = authors.replace('"', '')
    authors = authors.replace('`', '')
    authors = authors.replace('~', '')
    authors = authors.replace('^', '')
    return authors

def get_publication_name_with_booktitle(booktitle):
    # return the publication name from the booktitle
    # example: 
    # booktitle = "Proceedings of the 2023 ACM SIGSAC Conference on Computer and Communications Security"
    # return "CCS"
    if "SIGSAC Conference on Computer and Communications Security" in booktitle:
        return "CCS"
    else:
        raise ValueError("The booktitle is not recognized")

def add_paper_with_bib(bib_file_path):
    with app.app_context():
        bib_database = bibtexparser.parse_file(bib_file_path)
        new_paper_count = 0
        updated_paper_count = 0
        for entry in tqdm.tqdm(bib_database.entries):
            # Create a paper object from the entry
            create_result = create_paper_from_entry(entry)
            if create_result == 0:
                new_paper_count += 1
            else:
                updated_paper_count += 1
        db.session.commit()
        print(f"New papers added: {new_paper_count}")
        print(f"Papers updated: {updated_paper_count}")
        print(f"Total papers: {new_paper_count + updated_paper_count}")

def create_paper_from_entry(entry):
    # Create a paper object from a BibTeX entry
    # return 0 means the paper is new, return 1 means the paper is updated

    # print(entry)
    title = entry['title']
    authors = entry['author']
    authors = process_authors(authors)
    abstract = entry['abstract']
    publication_year = entry['year']
    publication_date = datetime.strptime(
            publication_year, "%Y"
        )  # Convert year to datetime
    publication_name = get_publication_name_with_booktitle(entry['booktitle'])
    publication_url = entry['url']

    # check if the paper already exists
    existing_paper = ResearchPaper.query.filter_by(
        title=title, authors=authors
    ).first()

    if existing_paper:
        update_existing_paper(
            existing_paper, publication_name, publication_date, publication_url, abstract,db=db
        )
        return 1
    else:
        new_paper = ResearchPaper(
            title=title,
            authors=authors,
            abstract=abstract,  # DBLP has no abstract information
            publication_name=publication_name,
            publication_date=publication_date,
            publication_url=publication_url,
        )
        db.session.add(new_paper)
        return 0



if __name__ == "__main__":
    start_time = time.time()
    parser = argparse.ArgumentParser(
        description="Parse a bib file and add the papers to the database."
    )
    parser.add_argument(
        "--bib_path", type=str, required=True, help="Path to the bib file."
    )
    args = parser.parse_args()
    add_paper_with_bib(args.bib_path)
    print(f"Execution time: {time.time() - start_time}")

