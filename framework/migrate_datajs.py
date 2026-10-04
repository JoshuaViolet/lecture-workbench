#!/usr/bin/env python3
"""
migrate_datajs.py: convert a legacy data.js (const flashcards = [...]; ...) into data.json.

Usage:
    python3 framework/migrate_datajs.py <subject_dir>

data.js was JavaScript source, so it is evaluated with Node to get the arrays; only
flashcards, mcqData and termLexicon are kept. Anything else (for example the old
psycDict) is reported and dropped. data.js itself is left in place.
"""
import json
import os
import subprocess
import sys

KEEP = ("flashcards", "mcqData", "termLexicon")

NODE_SCRIPT = r"""
const fs = require("fs");
const src = fs.readFileSync(process.argv[1], "utf8");
const names = [...src.matchAll(/\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=/g)].map(m => m[1]);
const values = new Function(src + "\nreturn {" + names.join(",") + "};")();
process.stdout.write(JSON.stringify(values));
"""


def main(argv):
    if len(argv) != 1:
        print(__doc__.strip().split("\n\n")[1])
        return 2
    subject = argv[0]
    src = os.path.join(subject, "data.js")
    dst = os.path.join(subject, "data.json")
    if not os.path.exists(src):
        print(f"no data.js in {subject}")
        return 1
    if os.path.exists(dst):
        print(f"{dst} already exists; remove it first if you want to regenerate it")
        return 1
    r = subprocess.run(["node", "-e", NODE_SCRIPT, src], capture_output=True, text=True)
    if r.returncode != 0:
        print("could not evaluate data.js with node:\n" + r.stderr.strip())
        return 1
    values = json.loads(r.stdout)
    data = {k: values[k] for k in KEEP if k in values}
    dropped = sorted(set(values) - set(KEEP))
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    counts = ", ".join(f"{k}={len(v)}" for k, v in data.items())
    print(f"wrote {dst} ({counts})" + (f"; dropped: {', '.join(dropped)}" if dropped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
