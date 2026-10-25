# Data artifacts

This repository intentionally excludes catalog images, source metadata, embeddings, and FAISS indexes.

Download the **Amazon Reviews 2023 Fashion metadata** JSONL export from the
[Amazon Reviews 2023 dataset](https://amazon-reviews-2023.github.io/), place it at
`data/raw/meta_Fashion.jsonl`, and start with the default 10,000-item subset.

The loader keeps products with a title and a usable image URL. Amazon's source price is frequently absent;
the `price` database column remains nullable rather than fabricating commercial data. Substitute a licensed
retailer catalog later if price-complete records are required for price-filter evaluation.
