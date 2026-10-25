from pathlib import Path
import faiss
import numpy as np
from backend.app.search_api.embedder import l2_normalize as n
from pipeline.embeddings import ClipEmbedder, product_text
from pipeline.dataset_loader import read_jsonl

A = "data/artifacts_v2/"
txt = n(np.load(A + "text_embeddings.npy"))
img = n(np.load(A + "image_embeddings.npy"))
cat = n(np.load(A + "catalog_embeddings.npy"))
ids = [str(x) for x in np.load(A + "product_ids.npy", allow_pickle=True).tolist()]
fa = faiss.read_index(A + "catalog.faiss")
fv = n(fa.reconstruct_n(0, fa.ntotal))
print("catalog.faiss rows vs catalog_embeddings.npy rows, mean cosine:",
      round(float((fv * cat).sum(1).mean()), 3))

row = {p: i for i, p in enumerate(ids)}
recs = [r for r in read_jsonl(Path("data/raw/catalog.jsonl")) if str(r.id) in row][:100]
emb = ClipEmbedder("ViT-B-32", "laion2b_s34b_b79k")
q = emb.encode_text([product_text(r) for r in recs], 32)
exp = np.array([row[str(r.id)] for r in recs])

for name, M in (("stored text ", txt), ("stored image", img),
                ("catalog.npy  ", cat), ("catalog.faiss", fv)):
    S = q @ M.T
    best = S.argmax(1)
    print(f"{name}: cos at expected row={S[np.arange(len(exp)), exp].mean():.3f}"
          f" | best-match cos={S.max(1).mean():.3f}"
          f" | best row is the expected row: {float((best == exp).mean()):.2f}")
