#!/usr/bin/env python3

"""
GXFR replicates DNS zone transfers by enumerating subdomains using advanced search engine queries
and conducting DNS lookups.

Original Author: Tim Tomes (LaNMaSteR53)
Ported to Python 3 and improved for modern compatibility.

Note on shebang:
  The original line '#!/usr/bin/python -tt' was used in Python 2 to enforce strict tab/space usage.
  In Python 3, the '-tt' option is deprecated and has no effect. This version uses the modern
  shebang: '#!/usr/bin/env python3'
"""

import sys
import os
import re
import time
import socket
import random
import json
import base64
import urllib.parse
import urllib.request

def print_banner():
    banner = '''
       _/_/_/  _/      _/  _/_/_/_/  _/_/_/   
    _/          _/  _/    _/        _/    _/  
   _/  _/_/      _/      _/_/_/    _/_/_/     
  _/    _/    _/  _/    _/        _/    _/    
   _/_/_/  _/      _/  _/        _/    _/     
'''
    print(banner)

def help():
    script = os.path.basename(sys.argv[0])
    return f"""gxfr.py - Tim Tomes (@LaNMaSteR53) (www.lanmaster53.com)

Syntax: python {script} domain [mode] [options]

MODES
=====
--gxfr [options]         GXFR mode
--bxfr [options]         BXFR mode (prompts for API key - required)
--both [options]         GXFR and BXFR modes

OPTIONS FOR ALL MODES
=====================
-h, --help               this screen
-o                       output results to a file
-v                       enable verbose mode
--dns-lookup             enable DNS lookups of all subdomains
--user-agent ['string']  set custom User-Agent string
--proxy [file|ip:port|-] use a proxy or list of proxies (randomized from list)
                         - file: a text file with ip:port per line
                         - '-': read list from stdin
                         - example: --proxy good.txt

OPTIONS FOR GXFR & BOTH MODES (GXFR shun evasion)
==================================================
-t [seconds]             wait between queries (default: 15)
-q [num]                 max number of queries (default: 0 = infinite)
--timeout [seconds]      set socket timeout (default: system default)

Examples:
  $ python {script} --bxfr --dns-lookup -o
  $ python {script} --both --dns-lookup -v
  $ python {script} --gxfr --dns-lookup --proxy open_proxies.txt --timeout 10
  $ python {script} --gxfr --dns-lookup -t 5 -q 5 -v --proxy 127.0.0.1:8080
  $ curl -O http://rmccurdy.com/scripts/proxy/good.txt && python {script} --both -t 0 --proxy good.txt --timeout 1
"""

def bxfr():
    print('[-] Resolving subdomains using the Bing API...')
    filename = 'api.keys'
    key = ''
    if os.path.exists(filename):
        print(f"[-] Extracting Bing API key from '{filename}'.")
        with open(filename, 'r') as f:
            for line in f:
                if 'bing::' in line:
                    key = line.split('::')[1].strip()
                    print(f"[-] Key found. Using '{key}'.")
                    break
        if not key:
            print('[!] No Bing API key found.')
    if not key:
        key = input('\nEnter Bing API key: ')
        with open(filename, 'a') as file:
            print(f"[-] Bing API key added to '{filename}'.")
            file.write(f'bing::{key}\n')
    creds = base64.b64encode(f':{key}'.encode()).decode()
    auth = f'Basic {creds}'
    base_query = f'site:{domain}'
    subs = []
    # test API key
    print('[-] Testing API key...')
    test_url = 'https://api.datamarket.azure.com/Data.ashx/Bing/Search/Web?Query=%27test%27&$top=50&$format=json'
    request = urllib.request.Request(test_url)
    request.add_header('Authorization', auth)
    request.add_header('User-Agent', user_agent)
    msg, content = sendify(request)
    if not content:
        if '401' in str(msg):
            print('[!] Invalid API key.')
            return []
        else:
            print('[-] Unable to test API key. Continuing anyway.')
    else:
        print('[-] API key is valid.')
    # execute API calls and parse json results
    # loop until no results are returned
    while True:
        try:
            query = ''
            for sub in subs:
                query += f' -site:{sub}.{domain}'
            full_query = f"'{base_query}{query}'"
            full_url = f'https://api.datamarket.azure.com/Data.ashx/Bing/Search/Web?Query={urllib.parse.quote_plus(full_query)}&$top=50&$format=json'
            if verbose:
                print(f'[+] using query: {full_url}...')
            request = urllib.request.Request(full_url)
            request.add_header('Authorization', auth)
            request.add_header('User-Agent', user_agent)
            if not verbose:
                sys.stdout.write('.')
                sys.stdout.flush()
            if proxy:
                msg, content = proxify(request)
            else:
                msg, content = sendify(request)
            if not content:
                break
            jsonobj = json.loads(content)
            results = jsonobj['d']['results']
            if len(results) == 0:
                print('[-] all available subdomains found...')
                break
            for result in results:
                url = result['Url']
                start = url.find('://') + 3
                end = url.find(domain) - 1
                sub = url[start:end]
                if sub not in subs:
                    if verbose:
                        print(f'[!] subdomain found: {sub}')
                    subs.append(sub)
        except KeyboardInterrupt:
            # catch keyboard interrupt and gracefully complete script
            break
    return subs

def gxfr():
    print('[-] Resolving subdomains using Google...')
    query_cnt = 0
    base_url = 'https://www.google.com'
    base_uri = '/m/search?'
    base_query = f'site:{domain}'
    pattern = f'>([\\.\\w-]*)\\.{domain}.+?<'
    subs = []
    new = True
    page = 0
    while new:
        try:
            query = ''
            for sub in subs:
                query += f' -site:{sub}.{domain}'
            full_query = base_query + query
            start_param = f'&start={page*10}'
            query_param = f'q={urllib.parse.quote_plus(full_query)}'
            if len(base_uri) + len(query_param) + len(start_param) < 2048:
                last_query_param = query_param
                params = query_param + start_param
            else:
                params = last_query_param[:2047 - len(start_param) - len(base_uri)] + start_param
            full_url = base_url + base_uri + params
            if verbose:
                print(f'[+] using query: {full_url}...')
            request = urllib.request.Request(full_url)
            request.add_header('User-Agent', user_agent)
            if not verbose:
                sys.stdout.write('.')
                sys.stdout.flush()
            if proxy:
                msg, result = proxify(request)
            else:
                msg, result = sendify(request)
            if not result:
                if '503' in str(msg):
                    print('[!] possible shun: use --proxy or find something else to do for 24 hours :)')
                break
            query_cnt += 1
            sites = re.findall(pattern, result)
            sites = list(set(sites))
            new = False
            for site in sites:
                if site not in subs:
                    if verbose:
                        print(f'[!] subdomain found: {site}')
                    subs.append(site)
                    new = True
            if max_queries and query_cnt >= max_queries:
                print('[-] maximum number of queries made...')
                break
            if not new:
                if 'Next page' not in result:
                    print('[-] all available subdomains found...')
                    break
                else:
                    page += 1
                    new = True
                    if verbose:
                        print(f'[+] no new subdomains found on page. jumping to result {page*10}.')
            if verbose:
                print('[+] sleeping to avoid lock-out...')
            time.sleep(secs)
        except KeyboardInterrupt:
            break
    print(f'[-] successful queries made: {query_cnt}')
    if verbose:
        print(f'[+] final query string: {full_url}')
    return subs

def sendify(request):
    requestor = urllib.request.build_opener()
    try:
        result = requestor.open(request)
        return "Success!'", result.read().decode('utf-8')
    except Exception as inst:
        try:
            if hasattr(inst, 'read') and inst.read().find('investigating the issue') == -1:
                print(f'[!] {inst}')
        except Exception:
            pass
        return inst, None

def proxify(request):
    while True:
        num = random.randint(0, len(proxies) - 1)
        host = proxies[num]
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({'https': host}))
        if verbose:
            print(f'[+] sending query to {host}')
        try:
            result = opener.open(request)
            return 'Success!', result.read().decode('utf-8')
        except Exception as inst:
            try:
                if hasattr(inst, 'code') and inst.code == 404 and inst.read().find('investigating the issue') != -1:
                    return inst, None
            except Exception:
                pass
            print(f'[!] {host} failed: {inst}.')
            if len(proxies) == 1:
                print('[-] valid proxy server not found.')
                return inst, None
            else:
                print(f'[!] removing {host} from proxy list.')
                del proxies[num]
