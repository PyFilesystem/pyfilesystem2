#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 17:30:33 2020

@author: pythonwood
"""

import shutil

_COLUMNS, _LINES = shutil.get_terminal_size((80, 20))

_WORDSEP = '  '

def words2lines(words, max_width=_COLUMNS):
    '''
words = ["a b", 'c', 'efg', 'hi', 'j']

max_width = 20  return ['"a b"  c  efg  hi  j']
max_width = 19  return ['"a b"  efg  j',
                        'c      hi'     ]
fallback each word is a line
    '''

    def wordsfix(_words):
        words = []
        for _word in _words:
            if " " in _word:
                word = '"%s"' % _word.replace('"', '\\"') # Python Wood  -> "Python Wood"
                words.append(word)
            else:
                words.append(_word)
        return words

    def build_result(words, wordfixlens, totalline):
        formats = [('%%-%ds' % i) for i in wordfixlens]
        result = []
        for linenum in range(totalline):
            _words = words[linenum::totalline]
            line = _WORDSEP.join(formats[i] % _words[i] for i in range(len(_words)))
            result.append(line)
        return result

    if not words:
        return []

    _words = words
    words = wordsfix(_words)

    minline = (len(_WORDSEP.join(words)) - 1) // max_width + 1

    for totalline in range(minline, len(words)+1):
        totalcol = (len(words) - 1) // totalline + 1 # if you have 10 words, totalline is 3 then you got 4 columns.
        colslens = []
        for coli in range(totalcol):
            coliwords = words[ coli*totalline : (coli+1)*totalline ]
            colslens.append(max(len(i) for i in coliwords))
        if sum(colslens) + len(_WORDSEP)*(len(colslens)-1) <= max_width:
            return build_result(words, colslens, totalline)

    return words    # fallback 1 word 1 line

if __name__ == '__main__':
    print('\n'.join(words2lines(['a b', 'c', 'efg', 'hi', 'j'], 20))) # 5 cols
    print('\n'.join(words2lines(['a b', 'c', 'efg', 'hi', 'j'], 19))) # 3 cols
    print('\n'.join(words2lines(['a b', 'c', 'efg', 'hi', 'j'], 7)))  # 1 cols
    print('\n'.join(words2lines(['a b'*i for i in range(20)])))  # _COLUMNS
