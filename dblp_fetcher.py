import requests
from bs4 import BeautifulSoup
import argparse
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from serve import ResearchPaper, db  # Adjust the import as necessary
import time
from datetime import datetime
from bs4.element import NavigableString
import unicodedata
import random
import tqdm
import bibtexparser

def normalize_authors(authors_str):
    normalized_authors = unicodedata.normalize('NFKD', authors_str)
    return ''.join([c for c in normalized_authors if not unicodedata.combining(c)])

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///papers.db"
db.init_app(app)

Implemented_Conferences_Journals = [
    "NDSS", "USENIX Security", "ICML"
]  # all the implemented conferences and journals are listed here

def get_abstract(publication_name, publication_url):
    if publication_name == "NDSS":
        return get_abstract_ndss(publication_url)
    elif publication_name == "USENIX Security":
        return get_abstract_usenix_security(publication_url)
    elif publication_name == "ICML":
        return get_abstract_icml(publication_url)
    else:
        print("Publication not implemented yet!")
        return ""  # Not implemented yet


def get_abstract_ndss(publication_url, debug=False):
    try:
        start_time = time.time()
        response = requests.get(publication_url)
        response.raise_for_status()  # Check that the request was successful
        if debug:
            print("Time taken for request: {:.2f} seconds".format(time.time() - start_time))
        start_time = time.time()
        soup = BeautifulSoup(response.text, "html.parser")
        main_content = soup.find("div", class_="paper-data")
        if debug:
            print("Time taken for parsing: {:.2f} seconds".format(time.time() - start_time))
        if not main_content:
            print(f"Page parsed and abstract is not found for {publication_url}")
            return "Abstract not found"

        abstract_paragraphs = main_content.find_all("p")
        # remove the paragraph that contains the title
        abstract_paragraphs = abstract_paragraphs[2:]
        abstract_text = []

        for paragraph in abstract_paragraphs:
            for content in paragraph.contents:
                if isinstance(content, NavigableString):
                    abstract_text.append(content.strip())
                elif content.name == "br":
                    abstract_text.append(" ")  # Replace <br> with space

        return " ".join(abstract_text).strip()
    except requests.RequestException as e:
        print(f"Error fetching the page: {e}")
        return None
    except Exception as e:
        print(f"Error parsing the page: {e}")
        return None

def get_abstract_usenix_security(publication_url, debug=False):
    try:
        start_time = time.time()
        response = requests.get(publication_url)
        response.raise_for_status()  # Check that the request was successful
        if debug:
            print("Time taken for request: {:.2f} seconds".format(time.time() - start_time))
        start_time = time.time()
        soup = BeautifulSoup(response.text, "html.parser")
        main_content = soup.find("div", class_="field field-name-field-paper-description field-type-text-long field-label-above")
        if debug:
            print("Time taken for parsing: {:.2f} seconds".format(time.time() - start_time))
        if not main_content:
            print(f"Page parsed and abstract is not found for {publication_url}")
            return "Abstract not found"

        abstract_paragraphs = main_content.find_all("p")
        abstract_text = []

        for paragraph in abstract_paragraphs:
            for content in paragraph.contents:
                if isinstance(content, NavigableString):
                    abstract_text.append(content.strip())
                elif content.name == "br":
                    abstract_text.append(" ")  # Replace <br> with space

        return " ".join(abstract_text).strip()
    except requests.RequestException as e:
        print(f"Error fetching the page: {e}")
        return None
    except Exception as e:
        print(f"Error parsing the page: {e}")
        return None


def get_abstract_icml(publication_url, debug=False):
    # for IMCL, the abstract can be found in the bibtex in the HTML, we parse the bibtex and get the abstract
    try:
        start_time = time.time()
        response = requests.get(publication_url)
        response.raise_for_status()  # Check that the request was successful
        if debug:
            print("Time taken for request: {:.2f} seconds".format(time.time() - start_time))
        start_time = time.time()
        soup = BeautifulSoup(response.text, "html.parser")
        bibtex_element = soup.find("code", id="bibtex")
        if debug:
            print("Time taken for parsing: {:.2f} seconds".format(time.time() - start_time))
        if not bibtex_element:
            print(f"Page parsed and abstract is not found for {publication_url}")
            return "Abstract not found"
        bibtex_text = bibtex_element.text
        library = bibtexparser.parse_string(bibtex_text)
        abstract_text = library.entries[0]['abstract']
        return abstract_text
    except requests.RequestException as e:
        print(f"Error fetching the page: {e}")
        return None
    except Exception as e:
        print(f"Error parsing the page: {e}")
        return None



def fetch_dblp_papers(dblp_url, publication_name, publication_year):
    with app.app_context():
        start_time = time.time()
        print(f"Fetching papers from DBLP URL: {dblp_url}")
        response = requests.get(dblp_url)
        # response = requests.get("https://dblp.org/db/conf/ndss/ndss2023.html")
        print("Time taken for request: {:.2f} seconds".format(time.time() - start_time))
        print(f"Response status code: {response.status_code}")
        start_time = time.time()
        soup = BeautifulSoup(response.text, "html.parser")
        print("Time taken for parsing: {:.2f} seconds".format(time.time() - start_time))
        publication_date = datetime.strptime(
            publication_year, "%Y"
        )  # Convert year to datetime
        print(
            f"The Publication date used default date of {publication_year}: {publication_date}"
        )
        total_paper_counter = 0
        new_paper_counter = 0
        updated_paper_counter = 0
        # for paper_li in soup.find_all("li", class_="entry inproceedings"):
        for paper_li in tqdm.tqdm(soup.find_all("li", class_="entry inproceedings")):
            total_paper_counter += 1
            title = paper_li.find("span", class_="title").text.strip()
            # title may ended with a unnecessary dot
            if title.endswith("."):
                title = title[:-1]
            authors = [
                author_span.text.strip()
                for author_span in paper_li.find_all("span", itemprop="author")
            ]
            publication_url = paper_li.find("a", itemprop="url")["href"]

            authors_str = ", ".join(authors)

            # get abstract if the publication is implemented
            if publication_name in Implemented_Conferences_Journals:
                abstract = get_abstract(publication_name, publication_url)  # TODO: add handler function
            else:
                abstract = ""
            # check if the paper already exists
            existing_paper = ResearchPaper.query.filter_by(
                title=title, authors=authors_str
            ).first()
            if total_paper_counter < 3:
                print(
                    f"Debug: \nTitle: {title}\nAuthors: {authors_str}\nPublication URL: {publication_url}\n Exsiting Paper: {existing_paper}\n Abstract: {abstract}"
                )
            if existing_paper:
                update_existing_paper(
                    existing_paper, publication_name, publication_date, publication_url, abstract
                )
                updated_paper_counter += 1
            else:
                if abstract is None or abstract == "Abstract not found":
                    print(f"Warning: Abstract not found for {title}. Skipping paper.")
                    continue

                new_paper = ResearchPaper(
                    title=title,
                    authors=authors_str,
                    abstract=abstract,  # DBLP has no abstract information
                    publication_name=publication_name,
                    publication_date=publication_date,
                    publication_url=publication_url,
                )
                new_paper_counter += 1
                db.session.add(new_paper)
                # Random delay between requests
            time.sleep(random.uniform(1.0, 5.0))
        print(
            f"Total papers fetched: {total_paper_counter}\nNew papers added: {new_paper_counter}\nExisting papers updated: {updated_paper_counter}"
        )
        try:
            db.session.commit()
        except Exception as e:
            print(f"Error during commit: {e}")



def update_existing_paper(existing_paper, publication_name, publication_date, publication_url, abstract, db=db):
    # print(f"Before update - Title: {existing_paper.title}, Pub Name: {existing_paper.publication_name}, Arxiv id: {existing_paper.arxiv_id}")
    existing_paper.publication_name = publication_name
    existing_paper.publication_date = publication_date
    existing_paper.publication_url = publication_url
    if abstract != "" and abstract != "Abstract not found" and abstract is not None:
        existing_paper.abstract = abstract
    
    db.session.add(existing_paper)




if __name__ == "__main__":
    start_time = time.time()
    parser = argparse.ArgumentParser(
        description="Fetch papers from DBLP and store them in the database."
    )
    parser.add_argument(
        "--url", type=str, required=True, help="DBLP URL to fetch data from"
    )
    parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="Publication name (conference/journal abbreviation)",
    )
    parser.add_argument("--year", type=str, required=True, help="Publication year")

    args = parser.parse_args()

    fetch_dblp_papers(args.url, args.name, args.year)
    print(
        f"Fetched papers from DBLP URL: {args.url} in {time.time() - start_time} seconds."
    )
