# Change Log
---
[0.0.2] - 2024-01-19

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
