#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nltk import edit_distance

import pandas as pd
import re
import os

from . import CodeBook

module_path = os.path.dirname(__file__)

class Lookup():
    
    # Need to finish this...
    lookupTable = pd.DataFrame()
    
    def __init__(self, master_list, fname=None):
        
        if fname:
            self.load(file)
            
        self.master_list = master_list
        
        return

    def findSimilarInSurvey(self, key, threshold=10):
        """
        Find questions within survey and within survey group that match.
        This is only supposed to account for survey questions that are similar, but answered
        as part of differing circumstances, e.g., married/split/etc.
        """
        
        key = key.strip()
        description = CodeBook.getCodeDescription(key)
        
        r = re.compile('([a-z]+[0-9]+[a-z])')
        m = r.match(key)
        
        if (not m) or description.startswith('SUSPECT'):
            print description
            return None, None
        
        group_key = m.groups()[0]
        print 'Matching for: {}'.format(group_key)
        print 'Description: {}'.format(description)
        
        candidates = self.master_list[map(lambda x: x.startswith(group_key), self.master_list)]
        
        def getScore(x,Y):
            score_list = []
            for y in Y:
                d = CodeBook.getCodeDescription(y)
                score = edit_distance(x,d)
                
                if (score < threshold) and (d != x):
                    score_list.append((y,score,d))
            
            score_list = sorted(score_list, key=lambda x: x[1])
            
            return score_list
        
        scores = getScore(description,candidates)
        
        if len(scores) > 0:
            print 'Matched Column: '
            print '\n'.join(['{} {} {}'.format(*x) for x in scores])
            return [x[0] for x in scores], scores
        
        return None, None
    
    def fillColumn(self, df, key):
        
        tryCols, scores = self.findSimilarInSurvey(key)
        
        if not tryCols:
            return df[key]
        
        def fillRow(x):
            if (x[key] < 0) and not (x[tryCols] < 0).all():
                return (x[tryCols][x[tryCols] >= 0]).mean() #not sure if this is best way...
            return x[key]
        
        new_col = df.apply(fillRow, axis=1)
         
        return new_col
    
    def save(self, fname):
        self.lookupTable.to_csv(os.path.join([module_path, './meta/{}.csv'.format(fname)]))
        return
    
    def load(self, fname):
        self.lookupTable = pd.read_csv(os.path.join([module_path, './meta/{}.csv'.format(fname)]))        
        return