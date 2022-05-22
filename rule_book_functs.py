import numpy as np
import pandas as pd
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
from nltk.stem import PorterStemmer as stemmer
from tqdm.notebook import tqdm

def tokenize(text):
    tokens = word_tokenize(text)
    tokens = [tok for tok in tokens if tok!='-']
    return tokens

def stem_text(text):
    return [stemmer().stem(w) for w in tokenize(text)]

def lemmatize_text(text):
    lemmatizer = nltk.stem.WordNetLemmatizer()
    return [lemmatizer.lemmatize(w) for w in tokenize(text)]

def tokenize(text):
    tokens = word_tokenize(text)
    tokens = [tok for tok in tokens if tok!='-']
    return tokens

def get_matches(keyword, tokens, span):
    # If the keyword matches a token, i will be where it occurs in the token string
    # You then apply the span before and after to create a keyword in context snipet
    matches = [(' '.join(tokens[max(0, i - span - 1):i + span + 1])) for i, tok in enumerate(tokens) if re.match(keyword, tok)]
    return(matches)

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
    
# Used for keyword in context approach
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
    # Extract contexts of keyword (if any found)
    # Four parts: [(pre), (keyword), (post), (all)]
    matches = [(
        ' '.join(tokens[max(0, i - window - 1): i]), tokens[i],
        ' '.join(tokens[i + 1:i + window + 1]),
        ' '.join(tokens[max(0, i - window - 1):i + window + 1])
        ) for i, tok in enumerate(tokens) if re.match(keyword, tok)]
    
    # do tests
    final_match = any([
        (check_presence(check_pre, pre) or check_presence(check_all, all_) or check_presence(check_post, post))
        and not check_presence(check_void, all_) for (pre, kw, post, all_) in matches
    ])
    return final_match    

# Rule book scanner function
def rule_book_scan(incidents, syn_dict, rules):
    
    finds_list = []
    finds_pats = []
    incid_nums = []
    incid_cats = []
    
    #for r in range(len(rules)):
    for r in range(3, 4, 1):
        
        rul_syns = tokenize(re.sub(r", ", " ", rules.syns[r]))
        
        pos_1st = syn_dict.get(rul_syns[0])
        pos_2nd = syn_dict.get(rul_syns[1])
        pos_3rd = syn_dict.get(rul_syns[2])
     
        # Connections between synonyms 1-2, 2-3
        connect = ['(.*)', '(.*)']

        # Shuffle rules
        srs = ([1, 0, 2], [])

        cat = rules.rule[r]
        
        span = rules.span[r]
        
        shuffle = rules.shuffle[r]
        
        voids = rules.voids[r]
        
        search_keyword = rules.keyword[r]

        console_str = f'Checking rule {r+1} of {len(rules)} ({cat})'
        print(console_str)
        print('='*len(console_str))
        for row in tqdm(range(len(incidents))):
            par_text = incidents.text[row].lower()
            # Check sentence by sentence, don't use span
            # TODO: Check impact of using span, should it be used or not?
            sen_toks = sent_tokenize(par_text)    
            irn = incidents.incident_id[row]
            for chk_text in sen_toks:
                
                # TODO: remove plurals, workers or worker's >>> worker
                for first_syn in pos_1st:
                    locals()["first_syn"] = first_syn.strip()
                    for second_syn in pos_2nd: 
                        for third_syn in pos_3rd:                              
                            
                            if search_keyword == '-':
                                
                                x = f'{first_syn.strip()}{connect[0]}{second_syn.strip()}{connect[1]}{third_syn.strip()}'
                                pattern = f'({x})'
                                check = check_presence(pattern, chk_text)
                                
                                for void in voids.split(sep = ', '):
                                    void_check = check_presence(void, chk_text)
                                    if void_check: break
                             
                                if check and not void_check: 
                                    print(f'{check}: {pattern}')
                                    finds_list.append(check)
                                    finds_pats.append(pattern)
                                    incid_nums.append(irn)
                                    incid_cats.append(cat)
                                    
                                else:
                                    for sr in srs:
                                        if len(sr) == 0: continue
                                        a = x.split(sep = connect[0])
                                        if shuffle == False:
                                                break
                                        # Adjust the word sequence using shuffle rule                             
                                        pattern = f'({a[sr[0]]}{connect[0]}{a[sr[1]]}{connect[1]}{a[sr[2]]})'
                                        rev_check = check_presence(pattern, chk_text)
                                        void_check = check_presence(void, chk_text)
                                                             
                                        if rev_check and not void_check:
                                            print(f'{rev_check}: {pattern} ---Shuffled')
                                            finds_list.append(rev_check)
                                            finds_pats.append(pattern)
                                            incid_nums.append(irn)
                                            incid_cats.append(cat)
                                
                            else:
                                test_tokens = tokenize(chk_text)
                                kwics = get_matches(search_keyword, test_tokens, span)
                            
                                for kwic in kwics:
                                    x = f'{first_syn.strip()}{connect[0]}{second_syn.strip()}{connect[1]}{third_syn.strip()}'
                                    pattern = f'({x})'
                                    check = check_presence(pattern, kwic)
                                    void_check = check_presence(void, chk_text)
                                     
                                    if check and not void_check: 
                                        print(f'{check}: {pattern}')
                                        finds_list.append(check)
                                        finds_pats.append(pattern)
                                        incid_nums.append(irn)
                                        incid_cats.append(cat)

                                    else:
                                        for sr in srs:
                                            if len(sr) == 0: continue
                                            a = x.split(sep = connect[0])
                                            if shuffle == False:
                                                break
                                            # Adjust the word sequence using shuffle rule                                            
                                            pattern = f'({a[sr[0]]}{connect[0]}{a[sr[1]]}{connect[1]}{a[sr[2]]})'
                                            rev_check = check_presence(pattern, chk_text)
                                            void_check = check_presence(void, chk_text)
                                            
                                            if rev_check and not void_check:  
                                                print(f'{rev_check}: {pattern} ---Shuffled')
                                                finds_list.append(rev_check)
                                                finds_pats.append(pattern)
                                                incid_nums.append(irn)
                                                incid_cats.append(cat)
                                            
        print('\n')
    out_df = pd.DataFrame(data=incid_nums, columns=['incid_nums'])
    out_df['finds_pats'] = finds_pats
    out_df['finds_list'] = finds_list
    out_df['incid_cats'] = incid_cats
    return(out_df)


def deepdive_results(dat, incidents_df, finds_df, focus='finds', ):
    for inc in dat.incident_id:
        sub_df = finds_df[finds_df.incid_nums == inc]
        sub_df = sub_df.drop(['finds_pats'], axis=1)
        cats = list(dict.fromkeys(sub_df.incid_cats))
        
        if focus == 'misses':
            bool_chk = len(cats) > 0
        else:
            bool_chk = len(cats) == 0
            
        if bool_chk:
            continue
        else:    
            par_text = incidents_df.text[incidents_df.incident_id == inc].values[0]   
            sen_toks = sent_tokenize(par_text)

            print(f'{inc} {cats}')
            print('='*len(inc))
            for sen in sen_toks: 
                print(sen)    
        print('\n')  