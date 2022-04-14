import re
from time import time
import pandas as pd
import numpy as np
from nltk.tokenize import word_tokenize
import nltk

incidents_fn = "../raw/lsr.xlsx"
rule_book_fn = "../raw/jason_myrules.csv"

def translate_to_regex(rule_part):
    """
    converts rule_book rules to regex format;
    drops trailing separators in process
    """
    if isinstance(rule_part, str):
        rule_part = re.sub(r"\s{2,}", " ", rule_part)
        rule_part = re.sub(r'\\\\b', r'\\b', rule_part)
        
        return r'(\b' + r'\b)|(\b'.join([s for s in rule_part.split('_ ') if s]) + r'\b)'
    else:
        return ''


def check_presence(pattern, string):
    if pattern:
        return bool(re.search(pattern, string))
    else:
        return False


def tokenize(text):
    tokens = word_tokenize(text)
    tokens = [tok for tok in tokens if tok!='-']
    return tokens


def find_pattern(tokens, keyword, check_pre, check_post, check_all, check_void, window):
    """
    for a list of tokens finds specified keyword and returns True
    if the neighbourhood of this keyword satisfies pre-, post- or all- context rules
    and doesn't contain anything forbidden
    :param tokens: list of tokens
    :param keyword: pattern which a token should match
    :param check_pre: pattern which several previous tokens (concatenated) should match
    :param check_post: pattern which several subsequent tokens (concatenated) should match
    :param check_all: pattern which previous tokens + keyword + subsequent tokens should match
    :param check_void: pattern which previous tokens + keyword + subsequent tokens should NOT match
    :param window: N of pre and post tokens to consider
    :return: True/False - whether at least one matching part was found
    """
    # extract contexts of keyword (if any found)
    matches = [(
        ' '.join(tokens[max(0, i - window - 1): i]),
        tokens[i],
        ' '.join(tokens[i + 1:i + window + 1]),
        ' '.join(tokens[max(0, i - window - 1):i + window + 1])
        ) for i, tok in enumerate(tokens) if re.match(keyword, tok)]
    
    # do tests
    final_match = any([
        (check_presence(check_pre, pre) or check_presence(check_all, all_) or check_presence(check_post, post))
        and not check_presence(check_void, all_) for (pre, kw, post, all_) in matches
    ])
    return final_match


def categorize_text(text_df, rules, window=5):
    """
    to each text (list of tokens) in a df assigns incident categories based on rules from rules df
    can assign several categories or none at all
    :param text_df: dataframe with a mandatory column "tokens" - list of strings, result of text tokenization
    :param rules: dataframe with rules (rule_book file)
    :param window: how may words to consider context
    :return: None, adds "categories" column to text_df, where categories are stored as concatenated strings
    """
    print('===========================================')
    print('Analysing free-text using rulebook approach')
    print('===========================================')
    tic = time()
    n = len(text_df)
    ruleCount = []
    # category indicators are stored in a bool array (n_texts, n_cats)
    # which is updated as the rules are checked
    categories = np.array(rules['group'].unique())
    cat_dict = {cat: i for i, cat in enumerate(categories)}
    category_indicators = np.full(shape=(n, len(categories)), fill_value=False)
    for i, row in rules.iterrows():
        finds = text_df['tokens'].apply(lambda x: find_pattern(
            tokens=x,
            keyword=row['keyword'],
            check_pre=row['rules_pre'],
            check_post=row['rules_post'],
            check_all=row['rules_all'],
            check_void=row['voids'],
            window=window
        ))
        category_indicators[:, cat_dict[row['group']]] = finds | category_indicators[:, cat_dict[row['group']]]
        
        print("Checking: {0} \t\t cat: ---{1}--- {2} occurences for rule {3}".format(row['keyword'], row['group'], sum(finds), i))
        ruleCount.append(sum(finds))
        
        #print(time() - toc)
    text_df['categories'] = [', '.join(categories[ind_row]) for ind_row in category_indicators]
    text_df['# of categories'] = [len(categories[ind_row]) for ind_row in category_indicators]
    rules['Count'] = ruleCount
    num_classified = (text_df['categories']!='').sum()
    percent = np.round(num_classified/n*100)
    summary = '{0} of {1} ({2}%) classified using rulebook'.format(num_classified, n, percent)
    print('='*len(summary))
    print(summary)
    print('='*len(summary))
    print(text_df['categories'][text_df['categories']!=''].value_counts())
    print('Time: {0}'.format(time() - tic))
    return(text_df)

my_test = 'fgfgee'
