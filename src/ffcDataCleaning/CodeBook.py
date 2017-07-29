#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib2 import urlopen

import pandas as pd
import json

        
response = urlopen('https://codalab.fragilefamilieschallenge.org/f/api/codebook/')
code_book = json.loads(response.read())
code_book = pd.DataFrame(code_book)
code_book = code_book.set_index('code')
    
def getCodeDescription(code):
    if code_book.index.isin([code]).any():
        return code_book.loc[code].description.encode('utf-8')
    else:
        return 'SUSPECT: No Description!'
    
