import os
import requests
from huggingface_hub import list_repo_files, hf_hub_url

REPO = "McAuley-Lab/Amazon-Reviews-2023"
N = 5000  # start small; raise to 20000-50000 later

files = list_repo_files(REPO, repo_type="dataset")
matches = [f for f in files if "meta_categories" in f and "Fashion" in f]
print("Matching files:", matches)

if not matches:
    print("No match found. Files under meta_categories:")
    for f in files:
        if "meta_categories" in f:
            print("  ", f)
    raise SystemExit(1)

filename = matches[0]
url = hf_hub_url(REPO, filename, repo_type="dataset")
print("Streaming from:", url)

os.makedirs("data/raw", exist_ok=True)
count = 0
with requests.get(url, stream=True, timeout=60) as r:
    r.raise_for_status()
    with open("data/raw/meta_Fashion.jsonl", "wb") as out:
        for line in r.iter_lines():
            if not line:
                continue
            out.write(line + b"\n")
            count += 1
            if count >= N:
                break

print(f"Saved {count} items to data/raw/meta_Fashion.jsonl")