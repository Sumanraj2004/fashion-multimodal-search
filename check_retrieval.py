import numpy as np

A = "data/artifacts_v2/"
n = lambda x: x / np.linalg.norm(x, axis=1, keepdims=True)
img, txt = n(np.load(A + "image_embeddings.npy")), n(np.load(A + "text_embeddings.npy"))

S = txt @ img.T                                  # row i: product i's text vs all images
rank = (S > np.diag(S)[:, None]).sum(1) + 1      # rank of the correct image
for k in (1, 5, 10):
    print(f"text->image recall@{k}:", round(float((rank <= k).mean()), 4))
print("median rank:", float(np.median(rank)))

print("distinct image vectors:", len(np.unique(np.round(img, 4), axis=0)), "of", len(img))
top = np.argsort(-S, axis=1)[:, :10]
counts = np.bincount(top.ravel(), minlength=len(img))
print("max times one image appears in a top-10:", int(counts.max()))
print("images never in any top-10:", int((counts == 0).sum()))
