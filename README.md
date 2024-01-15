# PaperHelper
A versatile tool designed to streamline the process of fetching and managing academic paper information. 

The project is still under development. The current version is a prototype that can fetch papers from Arxiv and display them in a web page.

## TODO:

- [x] Basic search function
- [x] Improve the search efficiency. The feature vectors may need to be stored out of database
- [ ] Show similar paper for a given paper
- [ ] Allow user to add tags to papers
- [ ] Allow user to receive recommendations based on tagged papers (like [arxiv-sanity-lite](https://github.com/karpathy/arxiv-sanity-lite))
- [ ] Fetch information from dblp and other sources like official websites of conferences
- [ ] Analysis page for a specific conference

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

You can fetch papers from Arxiv by running the following command. Note that this will fetch 20 papers from Arxiv with default query. You can change the default query in `arxiv_fetcher.py`.

```bash
python ./arxiv_fetcher.py --num 20 
```

You can also specify the query in the command. For example, the following command will fetch 20 papers with the query `cat:cs.CV` (Computer Vision).

```bash
python ./arxiv_fetcher.py --num 20 --query "cat:cs.CV"
```

The query can also be the name of a paper, just try it. For more information about constructing a query, check the [Arxiv API document](https://arxiv.org/help/api/user-manual#query_details).

### Compute feature vectors

Don't forget to computer feature vectors after fetching new papers. Without feature vectors, the search function will not work.

```bash
python ./compute_feature.py
```

### Search

Searching is implemented with simple but effective TF-IDF algorithm. You can search for papers in the web page. Try it yourself, don't forget to compute feature vectors first.

### Other Utilities

If you are a user of `arxiv-sanity-lite`, you can migrate your data to this project. First copy `migration_scripts/extract_asl_data.py` to the root of `arxiv-sanity-lite` and run it. Then copy the generated `data.json` to the root of this project. Finally, run the following command to migrate the data.

```bash
python ./asl_migration.py
```

It takes around 12 minutes to migrate 35k papers.



## Acknowledgement

This project is inspired by [arxiv-sanity-lite](https://github.com/karpathy/arxiv-sanity-lite). Thanks to the author for providing such a great tool.
