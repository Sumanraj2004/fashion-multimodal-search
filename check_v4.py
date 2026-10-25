from pathlib import Path
import numpy as np
from backend.app.search_api.embedder import ClipEmbedder as ApiEmb, l2_normalize as n
from pipeline.embeddings import ClipEmbedder as PipeEmb, product_text
from pipeline.dataset_loader import read_jsonl

A = "data/artifacts/"
txt = n(np.load(A + "text_embeddings.npy"))
ids = [str(x) for x in np.load(A + "product_ids.npy", allow_pickle=True).tolist()]
row = {p: i for i, p in enumerate(ids)}
recs = [r for r in read_jsonl(Path("data/raw/catalog.jsonl")) if str(r.id) in row][:6]

api = ApiEmb("ViT-B-32", "laion2b_s34b_b79k")
pipe = PipeEmb("ViT-B-32", "laion2b_s34b_b79k")
for r in recs:
    t = product_text(r)
    v_pipe = pipe.encode_text([t], 1)[0]
    v_api = api.embed_text(t)[0]
    s = txt[row[str(r.id)]]
    print(str(r.id),
          "| pipeline vs API embedder:", round(float(v_pipe @ v_api), 3),
          "| pipeline vs stored text:", round(float(v_pipe @ s), 3),
          "| API vs stored text:", round(float(v_api @ s), 3))