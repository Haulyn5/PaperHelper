# Note that this script is supposed to place in the arxiv-sanity-lite directory.
# Then run this script to get the exported data 'papers_data.json' in the same directory.

import json
from aslite.db import get_papers_db
from tqdm import tqdm

# Get the papers database
pdb = get_papers_db()

# Initialize an empty dictionary to store the paper data
papers_data = {}

# Iterate through the papers
for k, v in tqdm(pdb.items()):
    # Extract the required information
    title = v.get('title').replace('\n', ' ')
    authors = ', '.join(author['name'] for author in v.get('authors', []))
    abstract = v.get('summary')
    arxiv_upload_date = v.get('published')
    arxiv_categories = ', '.join(tag['term'] for tag in v.get('tags', []))

    # Store the information in the dictionary
    papers_data[k] = {
        'title': title,
        'authors': authors,
        'abstract': abstract,
        'arxiv_upload_date': arxiv_upload_date,
        'arxiv_categories': arxiv_categories,
    }

# Write the dictionary to a file
with open('papers_data.json', 'w') as f:
    json.dump(papers_data, f)