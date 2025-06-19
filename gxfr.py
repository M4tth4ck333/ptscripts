#!/usr/bin/env python3

"""
GXFR replicates DNS zone transfers by enumerating subdomains using advanced search engine queries
and conducting DNS lookups.
Original Author: Tim Tomes (LaNMaSteR53)
Ported to Python 3 and improved for modern compatibility.
m4tth4ck
Note on shebang:
  The original line '#!/usr/bin/python -tt' was used in Python 2 to enforce strict tab/space usage.
  In Python 3, the '-tt' option is deprecated and has no effect. This version uses the modern
  shebang: '#!/usr/bin/env python3'
"""

import sys
import os
import csv
import json
import sqlite3
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

leetdict = {
    'a': ['4', '@'],
    'e': ['3'],
    'g': ['6'],
    'i': ['1', '!'],
    'l': ['7', '1', '!'],
    'n': ['^'],
    'o': ['0'],
    'q': ['0'],
    's': ['5', '$'],
    't': ['7'],
    'v': ['\/'],
}

Base = declarative_base()

class WordVariant(Base):
    __tablename__ = 'variants'
    id = Column(Integer, primary_key=True)
    base = Column(String)
    variant = Column(String)

engine = create_engine('sqlite:///leetwords.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

def jtr(num):
    print('[List.Rules:Wordlist]')
    for key in leetdict.keys():
        for val in leetdict[key]:
            for i in range(int(num)):
                print('=%s%so%s%s' % (i, key, i, val))

def usage():
    print("""
leet.py - Tim Tomes (@LaNMaSteR53) (www.lanmaster53.com)

Usage:
  ./leet.py [options]
Options:
  -h                - This screen
  -c                - Swap case of all letters
  -f <file|->       - Wordlist to mangle. '-' is stdin
  -v                - View leet speak dictionary
  -b <#chars>       - Build JTR rule
  --output-format   - txt|json|csv|db
  --recon-ng-hook   - Print recon-ng CLI command
  --byknockulast    - Trigger ByKnockuLasT recon plugin
""")

def case(wordlist):
    for word in wordlist:
        for i in range(len(word)):
            chars = list(word)
            chars[i] = chars[i].swapcase()
            neword = ''.join(chars)
            if neword not in wordlist:
                wordlist.append(neword)
    return wordlist

def leet(wordlist):
    for word in wordlist:
        for i in range(len(word)):
            chars = list(word)
            if chars[i].lower() in leetdict.keys():
                for x in leetdict[chars[i].lower()]:
                    chars[i] = x
                    neword = ''.join(chars)
                    if neword not in wordlist:
                        wordlist.append(neword)
    return wordlist

def save_output(wordlist, baseword, fmt):
    if fmt == 'json':
        print(json.dumps({"base": baseword, "variants": sorted(wordlist)}, indent=2))
    elif fmt == 'csv':
        with open('output.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['Base', 'Variant'])
            for word in wordlist:
                writer.writerow([baseword, word])
    elif fmt == 'db':
        for word in wordlist:
            entry = WordVariant(base=baseword, variant=word)
            session.add(entry)
        session.commit()
        print(f"[+] Saved {len(wordlist)} entries to leetwords.db")
    else:
        for word in sorted(wordlist):
            print(word)

def recon_hooks(baseword):
    print("\n[Recon-ng CLI Hook]:")
    print(f"recon-cli -w leetword -m recon/domains-hosts/brute_hosts -x \"set WORDLIST /path/to/{baseword}.txt; run\"")
    print("\n[ByKnockuLasT CLI Stub]:")
    print("python3 byknockulast.py --import-list /path/to/leetwords.txt --mode=brute")

wordlist = []
baseword = ""
fmt = "txt"

def main():
    global wordlist, baseword, fmt

    if len(sys.argv) == 3 and sys.argv[1] == '-b':
        jtr(sys.argv[2])
        sys.exit()
    if len(sys.argv) == 2 and sys.argv[1] == '-v':
        for key in sorted(leetdict.keys()):
            print('%s:%s' % (key, ','.join(leetdict[key])))
        sys.exit()
    if '-h' in sys.argv:
        usage()
        sys.exit()

    if '--output-format' in sys.argv:
        fmt = sys.argv[sys.argv.index('--output-format') + 1]

    if '-f' in sys.argv and len(sys.argv) >= 3:
        filename = sys.argv[sys.argv.index('-f') + 1]
        if filename == '-':
            wordlist = sys.stdin.read().split()
        else:
            wordlist = open(filename).read().split()

    if '-c' in sys.argv:
        wordlist = case(wordlist)

    if not wordlist:
        usage()
        sys.exit()

    baseword = wordlist[0] if wordlist else "word"

    wordlist = leet(wordlist)
    save_output(wordlist, baseword, fmt)

    if '--recon-ng-hook' in sys.argv or '--byknockulast' in sys.argv:
        recon_hooks(baseword)

if __name__ == "__main__":
    main()
