# Change Log
---
## [0.0.3] - 2024-01-24

### Added

A setting page for the user to change the default query, the number of similar papers to show, search settings, etc.

A Navigation bar in the top of the page.

Semantic search based on [MiniLM](https://huggingface.co/sentence-transformers/all-MiniLM-L12-v2) which shows better performance than TF-IDF in most cases. 

Users now can select how to search papers: TF-IDF features, semantic features, or both.

### Changed

! Important: `feature_vectors.npz` renamed to `tf_idf_feature_vectors.npz`. Please rename the file manually if you have already run the previous version.

The style is modified, we will support theme selection in the future.

## [0.0.2] - 2024-01-19

### Added

An Edit page for the user to edit the information of a paper.

### Fixed

- <details>
<summary>Removed unnecessary spaces and line breaks in paper title and abstract.</summary>

The original ArxivFetcher will fetch the paper information with unwanted line breaks and spaces. We take a random paper as an example. For the constructed URL below, We will get the paper title `"ICTSurF: Implicit Continuous-Time Survival Functions with Neural\n  Networks"`, and many line breaks in the abstract. (You could try to open the URL in the browser.)

```
https://export.arxiv.org/api/query?search_query=ICTSurF+Implicit+Continuous-Time+Survival+Functions+with+Neural+Networks&max_results=3
```

So the ArxivFetcher before writes the wrong information to the database. We fix this by adding preprocessing to the paper information.
</details>

- A bug that similar score in the `similar` page is not correctly shown.
