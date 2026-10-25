import numpy as np

A = "data/artifacts/"
img = np.load(A + "image_embeddings.npy")
txt = np.load(A + "text_embeddings.npy")
cat = np.load(A + "catalog_embeddings.npy")
pid = np.load(A + "product_ids.npy", allow_pickle=True)
ipid = np.load(A + "index_product_ids.npy", allow_pickle=True)

def n(x):
    return x / np.linalg.norm(x, axis=1, keepdims=True)

img, txt, cat = n(img), n(txt), n(cat)
print("shapes:", img.shape, txt.shape, cat.shape, len(pid), len(ipid))
print("product_ids identical to index_product_ids:", bool((pid == ipid).all()))

perm = np.random.default_rng(0).permutation(len(img))
print("same-row image-text cosine :", round(float((img * txt).sum(1).mean()), 3))
print("random-pair image-text     :", round(float((img * txt[perm]).sum(1).mean()), 3))
print("random image-image cosine  :", round(float((img * img[perm]).sum(1).mean()), 3))
print("catalog vs image / vs text :", round(float((cat * img).sum(1).mean()), 3),
      round(float((cat * txt).sum(1).mean()), 3))
