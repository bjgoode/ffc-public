#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import os
import re

from . import CodeBook

module_path = os.path.dirname(__file__)

class Lookup():
    
    def __init__(self, master_list):
        self.master_list = master_list
        
        pairMatches = pd.DataFrame()

        for sId in range(1,6):
            heads = self.getRelatedColumnsMF(sId)
            df = self.getMatchPairIntervals(heads,sId)
            df['yearId'] = sId

            pairMatches = pd.concat((pairMatches,df), ignore_index=True)
        
        pairMatches = pairMatches.set_index(['motherSurvey', 'fatherSurvey'])
        self.pairMatches = pairMatches
        
        return
    
    def getRelatedColumnsMF(self, sId):
        """
        Reads column intervals specified in the mf-crossLookup.xlsx file.
        These column intervals have been verified to be correct and do cross-year
        matcing between mother and father surveys.

        Inputs:
        sId(int) - surveyId; {1,...,5}; corresponds to FFC labeling of m-f survey questionnaires.
        
        Output:
        heads(list) - list of related question Ids from surveys for given sId
        """

        fname = os.path.join(module_path, 'meta/mf-crossLookup.xlsx')
        wb = pd.ExcelFile(fname)

        md = {}

        md['1'] = wb.parse('M1')
        md['2'] = wb.parse('M2')
        md['3'] = wb.parse('M3')
        md['4'] = wb.parse('M4')
        md['5'] = wb.parse('M5')

        def parseCode(code,pre):
            col_code = code.split('-')
            col_code = [pre + "{}".format(sId) + m.lower().strip() for m in col_code]

            if len(col_code) == 1:
                col_start = col_code[0]
                col_stop = col_code[0]
            else:
                col_start = col_code[0]
                col_stop = col_code[1]

            return col_start, col_stop

        ws = md[str(sId)]

        heads = []

        for n, row in ws.iterrows():

            m_col_start, m_col_stop = parseCode(row[1],'m')
            f_col_start, f_col_stop = parseCode(row[2],'f')

            m_headers = "{}-{}".format(m_col_start, m_col_stop)
            f_headers = "{}-{}".format(f_col_start, f_col_stop)

            heads.append((m_col_start,m_col_stop, f_col_start, f_col_stop))

            #print "{} » {}".format(m_headers, f_headers)

        return heads

    def getColInterval(self, col_start, col_stop):

        def fixDigits(X):
            r = re.compile("([a-zA-Z]+)([0-9]+)([a-zA-Z]+)([0-9]+)(.*)")

            if isinstance(X,basestring): 
                In = [ X ]
            else:
                In = X

            out = []
            for x in In:
                #print x
                m = r.match(x)
                code = list(m.groups())
                #print 'Groups Found: '
                #print code
                if len(code[3]) == 1:
                    code[3] = '0'+code[3]

                out.append(''.join(code))

            if isinstance(X,basestring):
                return out[0]
            else:
                return out

        def common(x,y):  
            c = ""
            if (len(x) > 1) and (len(y) > 1) and (x[0] != '0') and (y[0] != '0') and (x[0] == y[0]):
                c = common(x[1:],y[1:])
            if (x[0] == y[0]) and (x[0] != '0') and (y[0] != '0'):
                return x[0] + c
            else:
                return c

        common_label = common(fixDigits(col_start), fixDigits(col_stop))
        cols = self.master_list[map(lambda x: x.startswith(common_label), self.master_list)]

        # First Check: Make fourth digit is numeric (weeds out all the other crap thrown in).
        cols = cols[map(lambda x: str.isdigit(x[3]), cols)]

        # Second Check: Make sure order is correct.
        cols = cols[map(lambda x: x >= fixDigits(col_start), fixDigits(cols))]
        cols = cols[map(lambda x: x <= fixDigits(col_stop)+'z', fixDigits(cols))]

        cols = sorted(cols, key = fixDigits)

        return cols


    def getMatchPairIntervals(self,heads,sId):

        cList = [
            'motherSurvey',
            'fatherSurvey',
            'm_desc',
            'f_desc',
        ]

        df = pd.DataFrame(columns = cList)

        with open(os.path.join(module_path,'../../output/matches_{}.txt'.format(sId)), 'w') as wFile:

            header = """
        #####################
            MATCHES: Year {}
        #####################\n\n\n\n
        """.format(sId)

            wFile.write(header)

            for mStart, mStop, fStart, fStop in heads:

                motherSurvey = self.getColInterval(mStart, mStop)
                fatherSurvey = self.getColInterval(fStart, fStop)

                #if len(motherSurvey) != len(fatherSurvey):
                    #print 'Length Mismatch!! m: {}, f: {}'.format(len(motherSurvey), len(fatherSurvey))

                m_descripton = map(CodeBook.getCodeDescription, motherSurvey)
                f_descripton = map(CodeBook.getCodeDescription, fatherSurvey)

                array = zip(motherSurvey, fatherSurvey, m_descripton, f_descripton)

                out_str =  '\n'.join(["""{:7} » {:7} | {}
                              | {}\n""".format(*x) for x in array])
                out_str += '---------------\n'

                #print out_str
                wFile.write(out_str)

                df = pd.concat((df,pd.DataFrame(array, columns=cList)), ignore_index=True)

            return df

    
    def findSimilarMFSurvey(self,key):
        
        if key.startswith('m'):
            level = 'motherSurvey'
        elif key.startswith('f'):
            level = 'fatherSurvey'
        else:
            return
        
        if not self.pairMatches.index.isin([key],level=level).any():
            return
        
        return self.pairMatches.xs(key, level=level).index.tolist()
    
    iterCount = 0
    def fillColumn(self, df, key):
        
        tryCols = self.findSimilarMFSurvey(key)
        
        self.iterCount += 1
        print 'Processing Column: {:10}, {:10}\r'.format(key,self.iterCount),
        
        if not tryCols:
            return df[key]
        
        def fillRow(x):
            if (x[key] < 0) and not (x[tryCols] < 0).all():
                return (x[tryCols][x[tryCols] >= 0]).mean() #not sure if this is best way...
            return x[key]
        
        new_col = df.apply(fillRow, axis=1)
         
        return new_col