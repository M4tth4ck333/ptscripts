#!/usr/bin/env python3

import sys

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
    'v': ['\\/'],
}

def jtr(num):
    print('[List.Rules:Wordlist]')
    for key in leetdict.keys():
        for val in leetdict[key]:
            for i in range(int(num)):
                print(f'={i}{key}o{i}{val}')

def usage():
    print("""
leet.py - Tim Tomes (@LaNMaSteR53) (www.lanmaster53.com)

Usage:
  ./leet.py [options]

Options:
  -h          - This screen
  -c          - Swap case of all letters
  -f <file|-> - Wordlist to mangle. '-' is stdin
  -v          - View leet speak dictionary
  -b <#chars> - Build a John The Ripper leet mangle rule for words <#chars> long.
                - Uses custom mangle dictionary as seen with '-v'
                - Not as thorough.
    """)

def case(wordlist):
    result = list(wordlist)  # preserve original
    for word in wordlist:
        for i in range(len(word)):
            chars = list(word)
            chars[i] = chars[i].swapcase()
            neword = ''.join(chars)
            if neword not in result:
                result.append(neword)
    return result

def leet(wordlist):
    result = list(wordlist)
    for word in wordlist:
        for i in range(len(word)):
            chars = list(word)
            if chars[i].lower() in leetdict:
                for x in leetdict[chars[i].lower()]:
                    chars[i] = x
                    neword = ''.join(chars)
                    if neword not in result:
                        result.append(neword)
    return result

def main():
    wordlist = []

    if len(sys.argv) == 3 and sys.argv[1] == '-b':
        jtr(sys.argv[2])
        sys.exit()

    if len(sys.argv) == 2 and sys.argv[1] == '-v':
        for key in sorted(leetdict.keys()):
            print(f'{key}:{",".join(leetdict[key])}')
        sys.exit()

    if '-h' in sys.argv:
        usage()
        sys.exit()

    if '-f' in sys.argv:
        try:
            filename = sys.argv[sys.argv.index('-f') + 1]
        except IndexError:
            usage()
            sys.exit()

        if filename == '-':
            wordlist = sys.stdin.read().split()
        else:
            with open(filename, 'r', encoding='utf-8') as f:
                wordlist = f.read().split()

    if '-c' in sys.argv:
        wordlist = case(wordlist)

    if not wordlist:
        usage()
        sys.exit()

    wordlist = leet(wordlist)
    for word in sorted(wordlist):
        print(word)

if __name__ == '__main__':
    main()
