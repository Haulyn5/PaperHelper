# PaperHelper
A versatile tool designed to streamline the process of fetching and managing academic paper information. 

The project is still under development. The current version is a prototype that can fetch papers from Arxiv and display them in a web page.

## TODO:

- [x] Basic search function
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

Then, open the browser and go to `http://localhost:5000/`.

For the first time, you may find that no paper was listed in the web page. You need to fetch papers from Arxiv first.

### Fetch from Arxiv

```bash
python arxiv_fetcher.py 20 # fetch 20 papers
```




