#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import re
import os

from itertools import permutations

module_path = os.path.dirname(__file__)

class Lookup():
    
    def __init__(self):
        
        inFile = './meta/year-mother-crossLookup.txt'
        motherSurvey_matches = self.parseCrossYearEntries(os.path.join(module_path, inFile))
        inFile = './meta/year-father-crossLookup.txt'
        fatherSurvey_matches = self.parseCrossYearEntries(os.path.join(module_path, inFile))
            
        self.pairMatches_mother = self.getPairMatches(motherSurvey_matches)
        self.pairMatches_father = self.getPairMatches(fatherSurvey_matches)
        
        return
    

    def parseCrossYearEntries(self, inFile):
        
        matches = {}
        r = re.compile(r'(-+|.*\s+)([0-9]+\.[0-9]+\s\s|-\s\s|$)(.*)')
        
        with open(inFile, 'r') as oFile:
            for line in oFile:
                line = line.strip()
                m = r.match(line)

                if m:
                    parsed = [x.strip() for x in m.groups()]

                    if not (parsed[0].startswith('*') or parsed[0].startswith('x') or parsed[0].startswith('--')):

                        if parsed[1] == '-':
                            entry_name = parsed[0]
                            parsed[1] = 0.0
                            entries = []
                        
                        parsed[1] = float(parsed[1])
                        entries.append(parsed)

                    elif parsed[0].startswith('--'):
                        if len(entries) > 1:
                            matches[entry_name] = entries

        return matches
    
    def getPairMatches(self,matches):
        
        pairMatches = pd.DataFrame()

        for k,vals in matches.iteritems():

            df = pd.DataFrame([{'key': v[0], 'score': v[1], 'desc': v[2]} for v in vals])
            df = df.set_index('key')

            perms = []
            for t,f in permutations(df.index,2):
                perms.append({
                    'to': t,
                    'from': f,
                    'score': abs(df.loc[t].score - df.loc[f].score),
                    'desc': df.loc[t].desc,
                })

            pairMatches = pd.concat([pairMatches,pd.DataFrame(perms)])

        pairMatches = pairMatches.set_index(['from', 'to'])
        return pairMatches
    
    
    def findSimilarCYSurvey(self,key):
        
        if key.startswith('m'):
            if not self.pairMatches_mother.index.isin([key],level='from').any():
                return
            return self.pairMatches_mother.xs(key, level='from').index.unique().tolist()
        
        elif key.startswith('f'):
            if not self.pairMatches_father.index.isin([key],level='from').any():
                return
            return self.pairMatches_father.xs(key, level='from').index.unique().tolist()
        
        return
    
    
    iterCount = 0
    def fillColumn(self, df, key):
        
        tryCols = self.findSimilarCYSurvey(key)
        
        self.iterCount += 1
        print 'Processing Column: {}, {:<10}\r'.format(key,self.iterCount),
        
        if not tryCols:
            return df[key]
        
        def fillRow(x):
            if (x[key] < 0) and not (x[tryCols] < 0).all():
                return (x[tryCols][x[tryCols] >= 0]).mean() #not sure if this is best way...
            return x[key]
        
        new_col = df.apply(fillRow, axis=1)
         
        return new_col