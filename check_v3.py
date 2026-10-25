import json
import numpy as np
from backend.app.search_api.embedder import ClipEmbedder, l2_normalize as n

A = "data/artifacts/"
img = n(np.load(A + "image_embeddings.npy"))
txt = n(np.load(A + "text_embeddings.npy"))
ids = [str(x) for x in np.load(A + "product_ids.npy", allow_pickle=True).tolist()]
row = {p: i for i, p in enumerate(ids)}
titles = {}
for line in open("data/raw/catalog.jsonl", encoding="utf-8"):
    r = json.loads(line)
    titles[str(r["id"])] = ((r.get("category") or "") + " " + (r.get("title") or "")).strip()
queries = json.load(open(A + "evaluation_queries.json", encoding="utf-8"))[:8]
emb = ClipEmbedder("ViT-B-32", "laion2b_s34b_b79k")

print("1) eval query text == catalog title of its relevant id?")
for x in queries[:5]:
    pid = x["relevant_product_ids"][0]
    print("  ", pid, titles.get(pid, "<missing>")[:60] == x["text"][:60])

print("2) fresh embedding of catalog title vs stored vectors")
for x in queries:
    pid = x["relevant_product_ids"][0]
    q = emb.embed_text(titles[pid])[0]
    print("  ", pid, "text", round(float(q @ txt[row[pid]]), 3), "image", round(float(q @ img[row[pid]]), 3))

print("3) same, but only the first 6 words of the title")
for x in queries[:4]:
    pid = x["relevant_product_ids"][0]
    q = emb.embed_text(" ".join(titles[pid].split()[:6]))[0]
    print("  ", pid, "text", round(float(q @ txt[row[pid]]), 3), "image", round(float(q @ img[row[pid]]), 3))

print("4) top image titles for 'black hoodie'")
q = emb.embed_text("black hoodie")[0]
for i in np.argsort(-(img @ q))[:3]:
    print("  ", titles[ids[i]][:80])