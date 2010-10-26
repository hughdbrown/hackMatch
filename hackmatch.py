#!/usr/bin/env python
# encoding: utf-8
# recognize.
"""
hackmatch.py

Created by Hilary Mason, Chris Wiggins, and Evan Korth.
Copyright (c) 2010 hackNY. All rights reserved.
"""
# pylint: disable=W0614
# pylint: disable=C0301

from collections import defaultdict
from optparse import OptionParser
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from hcluster import jaccard
from operator import itemgetter
from csv import DictReader

# startups: Name,E-mail,Company,In NYC,Funding,Site,Blog,Twitter,Num Employees,Environment,Project,Skills,Misc
# students: Student Name,e-mail,University,Major,Degree,Graduation Date,Site,Blog,Twitter,Facebook,Project,Skills,Misc

def get_stopwords():
    """
    get_stopwords: generate a list of stop words
    """
    return stopwords.words('english') + [',', '\xe2', '.', ')', '(', ':', "'s", "'nt", '\x99', '\x86', '\xae', '\x92']
        
def parse_csv(filename):
    """
    parse_csv: parses the CSV file to a dict
    """
    csv_reader = DictReader(open(filename))
    return [r for r in csv_reader]

def print_matches(matches, num_matches):
    """
    print_matches: print the top 'num_matches' matches
    """
    for key, value_dict in matches.items():
        print key
        all_matches = sorted(value_dict.items(), key=itemgetter(1))
        top_matches = all_matches[-num_matches:]
        # pylint: disable=W0612
        for item, score in top_matches:
            print "\t%(item)s :: %(score)s" % locals()
            # print "'%s' '%s' %s" % (n.translate(string.maketrans("",""), string.punctuation), item.translate(string.maketrans("",""), string.punctuation), score)
        # pylint: enable=W0612
        print '\n'

class HackMatch(object):
    """
    HackMatch: class to encapsulate matching companies versus startups on selected fields
    """
    DEBUG = False
    BOW_FIELDS = ['Environment', 'Project', 'Skills', 'Misc']
    COMPLETENESS_THRESHOLD = 4 # num of words necessary to match
    
    def __init__(self, student_file, startup_file, num_matches=3, distance=jaccard):
        self.stopwords = set(get_stopwords())
        self.distance = distance
        
        student_data = parse_csv(student_file)
        startup_data = parse_csv(startup_file)
        
        doc_words = self.define_features([student_data, startup_data], self.BOW_FIELDS)

        # matches = self.do_ranking(student_data, startup_data, doc_words, self.BOW_FIELDS, base_name_field='Student Name', match_name_field='Company')
        matches = self.do_ranking(startup_data, student_data, doc_words, self.BOW_FIELDS)

        print_matches(matches, num_matches)
    
    # pylint: disable=R0913
    def do_ranking(self, base_data, match_data, doc_words, fields=None, base_name_field='Company', match_name_field='Student Name'):
        """
        do ranking
        """
        fields = fields or []
        base = dict((item[base_name_field], self.extract_features(item, doc_words, fields)) for item in base_data)

        matches = defaultdict(dict)
        for match_item in match_data:
            match_features = self.extract_features(match_item, doc_words, fields)
            temp_dict = matches[match_item[match_name_field]]
            for base_item, base_item_features in base.items(): # actually do the comparison
                if not base_item_features or not match_features:
                    temp_dict[base_item] = 0.0
                else:
                    temp_dict[base_item] = self.distance(base_item_features, match_features)
                if self.DEBUG:
                    print "%s :: %s = %s " % (match_item[match_name_field], base_item, self.distance(base_item_features, match_features))

        return matches

    def extract_features(self, item_dict, doc_words, fields=None):
        """
        extract_features: Determine whether features pass test
        """
        fields = fields or []
        tokeniter = (item_dict[f] for f in fields if f in item_dict)
        s_tokens = reduce(list.extend, tokeniter)
        s_features = [token in s_tokens for token in doc_words]
        return s_features if sum(s_features) > self.COMPLETENESS_THRESHOLD else None

    def define_features(self, data, fields=None):
        """
        define the global bag of words features
        """
        fields = fields or []
        ngram_freq = defaultdict(int)
        
        featureiter = (
            r[f]
            for d in data
            for r in d
            for f in fields
            if f in r
        )
        for field in featureiter:
            tokeniter = (word.lower() for word in word_tokenize(field))
            legaliter = (word.strip('.') for word in tokeniter if word not in self.stopwords)
            for legal_word in legaliter:
                ngram_freq[legal_word] += 1
                            
        ngram_freq = dict((word, word_count) for word, word_count in ngram_freq.items() if word_count > 1)
        if self.DEBUG:
            print "Global vocabulary: %s" % len(ngram_freq)        
        return ngram_freq
    

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-n", "--number", action="store", type="int", dest="num_matches", default=10, help="number of results to return")
    parser.add_option("-s", "--student", action="store", type="string", dest="student_file", default="unmatched_students.csv", help="csv of student data")
    parser.add_option("-t", "--startup", action="store", type="string", dest="startup_file", default="unmatched_top_startups.csv", help="csv of startup data")
    (options, args) = parser.parse_args()
    
    hackmatch = HackMatch(num_matches=options.num_matches, student_file=options.student_file, startup_file=options.startup_file)
