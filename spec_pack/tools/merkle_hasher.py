import argparse
import json
import hashlib
import os
import sys

def hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser(description="Merkle Hasher for Proof Artifacts")
    parser.add_argument("--in", dest="inp", required=True, help="Input directory containing proof artifacts.")
    parser.add_argument("--out", required=True, help="Output file for the Merkle root JSON.")
    args = parser.parse_args()

    if not os.path.isdir(args.inp):
        print(f"Error: Input path {args.inp} is not a directory.", file=sys.stderr)
        sys.exit(1)

    hashes = []
    for root, _, files in os.walk(args.inp):
        for filename in sorted(files):
            if filename == os.path.basename(args.out): # Don't hash the output file itself
                continue
            path = os.path.join(root, filename)
            hashes.append(hash_file(path))
    
    # Simple Merkle root: hash of sorted concatenated hashes
    merkle_root = hashlib.sha256("".join(sorted(hashes)).encode()).hexdigest()

    with open(args.out, "w") as f:
        json.dump({"merkle_root": merkle_root, "files_hashed": len(hashes)}, f, indent=2)

    print(f"Merkle root calculated and saved to {args.out}")

if __name__ == "__main__":
    main()