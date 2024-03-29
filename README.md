# PaperHelper

PaperHelper is a versatile tool designed to streamline the process of fetching and managing academic paper information. It aims to enhance the experience of researchers and students by providing efficient access to relevant papers and facilitating various paper-related tasks.

This project draws inspiration from [arxiv-sanity-lite](https://github.com/karpathy/arxiv-sanity-lite) and aims to offer even more features. For now, one notable improvement is the utilization of semantic feature vectors, which enables PaperHelper to outperform arxiv-sanity-lite in finding similar papers.

The current version of PaperHelper is a functional prototype that successfully fetches papers from Arxiv and DBLP, and presents them in a web page. However, please note that the project is still under active development, and additional features and improvements are planned.

## TODO:

- [x] Basic search function
- [x] Improve search efficiency by storing feature vectors in a separate file outside the database.
- [x] Show similar papers for a given paper using feature vectors.
- [x] Fetch information from DBLP database.
- [x] Implement an Edit page for users to modify paper information.
- [x] Incorporate semantic embedding methods like MiniLM for enhanced performance.
- [x] Develop a Settings page for users to configure default queries, the number of similar papers to display, ranking parameters, and more.
- [x] Enhance search results by incorporating the effective search method from arxiv-sanity-lite as Match, which users can select in the Settings page.
- [x] Add paper from bib file.
- [ ] Automatically generate keywords for paper.
- [ ] Filter papers by author name, publication, year, etc.
- [ ] Implement abstract parsing for additional conferences.
- [ ] Create a page to allow users to manually compute feature vectors.
- [ ] Enable users to add tags to papers.
- [ ] Provide recommendations based on tagged papers, similar to arxiv-sanity-lite.
- [ ] Develop an Analysis page for specific conferences.

## Installation

We recommend using `conda` to manage the environment. 

```bash
conda create -n paper_helper python=3.11
```

Then, activate the environment and install the dependencies.

```bash
conda activate paper_helper
pip install -r requirements.txt
```


## Usage

Please change the directory to the root of the project before running the following commands.

### Start the server

```bash
python ./serve.py
```

Then, open the browser and go to `http://localhost:40500/`. (The default port is 40500, you can change it in `serve.py`)

For the first time, you may find that no paper was listed in the web page. You need to fetch papers from Arxiv first.

### Fetch from Arxiv

You can fetch papers from Arxiv by running the following command. Note that this will fetch 20 papers from Arxiv with default query. You can change the default query in the settings page.

```bash
python ./arxiv_fetcher.py --num 20 
```

You can also specify the query in the command. For example, the following command will fetch 20 papers with the query `cat:cs.CV` (Computer Vision).

```bash
python ./arxiv_fetcher.py --num 20 --query "cat:cs.CV"
```

The query can also be the name of a paper, just try it. For more information about constructing a query, check the [Arxiv API document](https://arxiv.org/help/api/user-manual#query_details).

Maybe you want to fetch papers periodically to keep the database up to date. (We will add helper scripts for this in the future)

### Compute feature vectors

Don't forget to computer feature vectors after fetching new papers. Without feature vectors, the search function will not work.

```bash
python ./compute_feature.py
```

### Search

You can now search for papers with 4 methods/ features: `Match`, `TF-IDF`, `Semantic` and `Combination`. You can change the default search method in the settings page. 

- `Match` is the search method used in [arxiv-sanity-lite](https://github.com/karpathy/arxiv-sanity-lite/blob/master/serve.py#L172C5-L172C16)
- `TF-IDF` is the search method used in the previous version of this project. Simple but effective. Implemented with [scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
- `Semantic` is the search method based on [MiniLM](https://huggingface.co/sentence-transformers/all-MiniLM-L12-v2). It shows better performance than TF-IDF in most cases.
- `Combination` is the combination of `TF-IDF`, `Semantic` and `Match`. It is the default search method. You can also set the weight of each method in the settings page.

### Similar papers

You can find similar papers for a given paper in the web page. For how many similar papers to show, you can change the it in the settings page.  The similar papers is found by purely semantic features.

### Fetch from dblp

DBLP does not provide abstract information for the papers. Therefore, this script also obtains the abstract from the official web page of the paper, if possible. However, this requires a separate script for each conference (if they are hosted on different websites) to parse the abstract of the paper.

This script supports the following publications (for now):

- NDSS (2022, 2023 tested)
- USENIX Security (2023 tested)
- ICML (2023 tested)

To fetch papers from DBLP, run the provided command, but ensure you correctly input the conference’s URL, name, and year. The script doesn’t validate inputs, so be careful.

We tested S&P 2023 and found that the page is dynamically generated, and parsing the page is not easy. We leave it to the future.

#### Command

```bash 
python dblp_fetcher.py --url "https://dblp.org/db/conf/ndss/ndss2022.html" --name "NDSS" --year "2022"
```

### Add paper from bib files (Alpha feature)

You can add papers from bib files. This feature may be not stable and is intended for adding papers from ACM Digital Library.  

This script supports the following publications (for now):

- CCS (2023 tested)

#### Command

```bash
python .\add_paper_with_bib.py --bib_path "path_to_the_bib_file.bib"
```

### Semantic Search

We implement semantic search with [all-MiniLM-L12-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L12-v2). With semantic search, you can search for papers with similar meaning. 

In our test, it takes around 1 second to process 30 papers with an i7-9700 CPU.

### Other Utilities

If you are a user of `arxiv-sanity-lite`, you can migrate your data to this project. First copy `migration_scripts/extract_asl_data.py` to the root of `arxiv-sanity-lite` and run it. Then copy the generated `data.json` to the root of this project. Finally, run the following command to migrate the data.

```bash
python ./asl_migration.py
```

It takes around 12 minutes to migrate 35k papers.

## Known issues

- DBLP stored the authors name in English, but Arxiv stored the authors name in their native language. For example, the name of the author "Bădoiu" is stored as "Badoiu" in DBLP. This will cause the same author to be treated as different authors. We now use normalization to solve this problem. 
- The same paper will be have different title in DBLP and Arxiv. (Though the difference is small) We hope we will add a merge function in the future to solve this problem.

## Acknowledgement

This project is inspired by [arxiv-sanity-lite](https://github.com/karpathy/arxiv-sanity-lite). Thanks to the author for providing such a great tool.
