# PaperHelper
A versatile tool designed to streamline the process of fetching and managing academic paper information. 

The project is still under development. The current version is a prototype that can fetch papers from Arxiv and display them in a web page.

## TODO:

- [x] Basic search function
- [ ] Show similar paper for a given paper
- [ ] Allow user to add tags to papers
- [ ] Allow user to receive recommendations based on tagged papers (like arxiv-sanity-lite)
- [ ] Fetch information from dblp and other sources like official websites of conferences
- [ ] Analysis page for a specific conference


## Usage

Please change the directory to the root of the project before running the following commands.

### Fetch from Arxiv

```
python arxiv_fetcher.py 20 # fetch 20 papers
```

### Start the server

```
python ./serve.py
```

Then, open the browser and go to `http://localhost:5000/`.

