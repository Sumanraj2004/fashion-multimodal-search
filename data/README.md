# Data artifacts

The deployment catalog is checked in at `data/raw/catalog.jsonl`; its matching FAISS index and product IDs
are checked in at `data/artifacts_v2/catalog.faiss` and `data/artifacts_v2/index_product_ids.npy`. These
three files are the runtime inputs for the Docker search application.

Catalog images, source metadata, generated embeddings, and other intermediate artifacts are not included.

Download the **Amazon Reviews 2023 Fashion metadata** JSONL export from the
[Amazon Reviews 2023 dataset](https://amazon-reviews-2023.github.io/), place it at
`data/raw/meta_Fashion.jsonl`, and start with the default 10,000-item subset.

The loader keeps products with a title and a usable image URL. Amazon's source price is frequently absent;
the `price` database column remains nullable rather than fabricating commercial data. Substitute a licensed
retailer catalog later if price-complete records are required for price-filter evaluation.
