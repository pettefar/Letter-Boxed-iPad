#!/usr/bin/env python3
"""
Letter Boxed solver.
Usage:
    python3 letterboxed.py abc def ghi jkl
    python3 letterboxed.py abc def ghi jkl --dict /path/to/words.txt --max-words 2 --limit 20  (2 is the default)

Rules:
  * 12 letters, 4 sides of 3.
  * Consecutive letters in a word must come from DIFFERENT sides.
  * Each word after the first starts with the last letter of the previous one.
  * Every letter must be used at least once across all words.
"""
import argparse
import os
import sys
import urllib.request
from collections import defaultdict

DICT_URL = "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"
SYSTEM_DICTS = [
    "/usr/share/dict/words",
    "/usr/share/dict/british-english",
    "/usr/share/dict/american-english",
]
CACHE_FILE = "words_alpha.txt"


def load_words(path=None):
    """Load a word list from path, the system dictionary, or download one."""
    if path is None:
        for p in SYSTEM_DICTS:
            if os.path.exists(p):
                path = p
                break
    if path is None:
        if not os.path.exists(CACHE_FILE):
            print(f"No dictionary found, downloading to {CACHE_FILE} ...", file=sys.stderr)
            urllib.request.urlretrieve(DICT_URL, CACHE_FILE)
        path = CACHE_FILE
    print(f"Using dictionary: {path}", file=sys.stderr)
    with open(path, encoding="utf-8", errors="ignore") as f:
        return {w.strip().lower() for w in f if w.strip().isalpha()}


def valid_words(words, sides, min_len=3):
    """Words buildable on the box: only box letters, never two in a row from one side."""
    side_of = {ch: i for i, s in enumerate(sides) for ch in s}
    out = []
    for w in words:
        if len(w) < min_len:
            continue
        if any(ch not in side_of for ch in w):
            continue
        if any(side_of[a] == side_of[b] for a, b in zip(w, w[1:])):
            continue
        out.append(w)
    return out


def solve(words, sides, max_words=3, limit=20):
    letters = "".join(sides)
    bit = {ch: 1 << i for i, ch in enumerate(letters)}
    full = (1 << len(letters)) - 1

    def mask(w):
        m = 0
        for ch in w:
            m |= bit[ch]
        return m

    # Speed trick: words with same (first, last, letters-used) are interchangeable
    # for the search, so keep the longest as the representative.
    reps = {}
    for w in words:
        key = (w[0], w[-1], mask(w))
        if key not in reps or len(w) > len(reps[key]):
            reps[key] = w

    by_first = defaultdict(list)
    for (first, _last, m), w in reps.items():
        by_first[first].append((w, m))
    for lst in by_first.values():
        lst.sort(key=lambda t: -bin(t[1]).count("1"))  # most-covering first

    solutions = []

    def dfs(chain, covered, depth_left):
        if len(solutions) >= limit:
            return
        if depth_left == 0:
            return
        starts = [chain[-1][-1]] if chain else list(by_first)
        for s in starts:
            for w, m in by_first.get(s, []):
                new = covered | m
                if new == full:
                    if depth_left >= 1:
                        solutions.append(chain + [w])
                        if len(solutions) >= limit:
                            return
                elif depth_left > 1:
                    dfs(chain + [w], new, depth_left - 1)

    # Fewest words first
    for n in range(1, max_words + 1):
        dfs([], 0, n)
        # dfs finds chains up to n words; stop once we have enough
        if solutions:
            break
    # Dedupe, sort by word count then total length
    uniq = sorted({tuple(s) for s in solutions}, key=lambda s: (len(s), sum(map(len, s))))
    return uniq


def main():
    print("Trying to solve in two words...")
    ap = argparse.ArgumentParser(description="Letter Boxed solver")
    ap.add_argument("sides", nargs=4, help="four 3-letter sides, e.g. abc def ghi jkl")
    ap.add_argument("--dict", help="path to a word list (one word per line)")
    ap.add_argument("--max-words", type=int, default=2)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--min-len", type=int, default=3)
    args = ap.parse_args()

    sides = [s.lower() for s in args.sides]
    letters = "".join(sides)
    if any(len(s) != 3 for s in sides) or len(set(letters)) != 12 or not letters.isalpha():
        sys.exit("Need 4 sides of 3 letters, 12 different letters in total.")

    words = valid_words(load_words(args.dict), sides, args.min_len)
    print(f"{len(words)} usable words on this box", file=sys.stderr)

    sols = solve(words, sides, args.max_words, args.limit)
    if not sols:
        print("No solutions found. Try --max-words 3 or a bigger dictionary.")
        return
    for s in sols:
        print(" -> ".join(s))


if __name__ == "__main__":
    main()
