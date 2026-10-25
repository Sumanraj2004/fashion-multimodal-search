import json
import numpy as np
from backend.app.search_api.embedder import ClipEmbedder, l2_normalize

A = "data/artifacts/"
n = l2_normalize
img = n(np.load(A + "image_embeddings.npy"))
txt = n(np.load(A + "text_embeddings.npy"))
ids = [str(x) for x in np.load(A + "product_ids.npy", allow_pickle=True).tolist()]
row = {p: i for i, p in enumerate(ids)}
queries = json.load(open(A + "evaluation_queries.json", encoding="utf-8"))[:40]
emb = ClipEmbedder("ViT-B-32", "laion2b_s34b_b79k")
PREFIX = "AMAZON FASHION "

variants = [
    ("stripped", lambda t: t[len(PREFIX):] if t.startswith(PREFIX) else t),
    ("with prefix", lambda t: t),
]
for label, fn in variants:
    q = np.vstack([emb.embed_text(fn(x["text"])) for x in queries])
    r = [row[x["relevant_product_ids"][0]] for x in queries]
    S = q @ img.T
    rank = (S > S[np.arange(len(r)), r][:, None]).sum(1) + 1
    print(label)
    print("  cosine to stored text vector :", round(float((q * txt[r]).sum(1).mean()), 3))
    print("  cosine to stored image vector:", round(float((q * img[r]).sum(1).mean()), 3))
    print("  recall@10 text->image        :", round(float((rank <= 10).mean()), 3))