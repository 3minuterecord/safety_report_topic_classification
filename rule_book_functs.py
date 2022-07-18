import numpy as np
import pandas as pd
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
from nltk.stem import PorterStemmer as stemmer
#from tqdm.notebook import tqdm
from tqdm import tqdm
from datetime import datetime
import sys


def isNaN(num):
    return num!= num

def remove_dups(ent):
    split_ent = ent.split(', ')
    uniqe_ent = list(dict.fromkeys(split_ent))
    rjoin_ent = ", ".join(uniqe_ent)
    return(rjoin_ent)

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

# Used for basic keyword in context approach
def find_pattern_basic(tokens, keyword, check_pre, check_post, check_all, check_void, window):
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

# Used for keyword in context approach (more robust context extraction)
def find_pattern(doc, keyword, check_pre, check_post, check_all, check_void, window):
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
    # check if keyword in sentence
    any_match = re.search(keyword, doc)

    if any_match is None:
        return False
    else:
        # We want to finad and extract the context of the keyword in the sentence
        # With a predefined window
        pre_context = "(?:[a-zA-Z'-]+[^a-zA-Z'-]+){0,<window>}<keyword>".replace('<keyword>', str(keyword)).replace('<window>', str(window))
        post_context = "<keyword>(?:[^a-zA-Z'-]+[a-zA-Z'-]+){0,<window>}".replace('<keyword>', str(keyword)).replace('<window>', str(window))
        all_context = "(?:[a-zA-Z'-]+[^a-zA-Z'-]+){0,<window>}<keyword>(?:[^a-zA-Z'-]+[a-zA-Z'-]+){0,<window>}".replace('<keyword>', str(keyword)).replace('<window>', str(window))
        
        pre_match = re.findall(pre_context, doc)
        post_match = re.findall(post_context, doc)
        all_match = re.findall(all_context, doc)

    # Check if any of the given sentences is on list of pre/post/all keywords.
    pre_check = any([check_presence(check_pre, pre) for pre in pre_match])
    post_check = any([check_presence(check_post, post) for post in post_match])
    all_check = any([check_presence(check_all, all_) for all_ in all_match])
    void_check = any([check_presence(check_void, all_) for all_ in all_match])

    # Perform final tests
    final_match = (pre_check or post_check or all_check) and not void_check
    return final_match

# Function to categorize text using simple find pattern approach
def categorize_text(doc, rules, window=5):
    """
    to each text (list of tokens) in a df assigns incident categories based on rules from rules df
    can assign several categories or none at all
    :param text_df: dataframe with a mandatory column "tokens" - list of strings, result of text tokenization
    :param rules: dataframe with rules (rule_book file)
    :param window: how may words to consider context
    :return: None, adds "categories" column to text_df, where categories are stored as concatenated strings
    """

    # Category indicators are stored in a bool array (n_texts, n_cats)
    # which is updated as the rules are checked
    categories = list(set(rules["group"])) # Use set to remove duplicate groups (each group can have > 1 rule)

    cat_dict = {cat: i for i, cat in enumerate(categories)}
    category_indicators = [False] * len(categories)

    num_rules = len(rules['group'])

    for i in range(num_rules):
        finds = find_pattern(
            doc=doc,
            keyword=rules["keyword"][i],
            check_pre=rules["rules_pre"][i],
            check_post=rules["rules_post"][i],
            check_all=rules["rules_all"][i],
            check_void=rules["voids"][i],
            window=window,
        )

        # Update if found, True | False >>> True
        category_indicators[cat_dict[rules["group"][i]]] = (
            finds | category_indicators[cat_dict[rules["group"][i]]]
        )

    finds = [
        (
            rules['group'][j],
            find_pattern(
                doc=doc,
                keyword=rules["keyword"][j],
                check_pre=rules["rules_pre"][j],
                check_post=rules["rules_post"][j],
                check_all=rules["rules_all"][j],
                check_void=rules["voids"][j],
                window=window,
            )
        ) for j in range(num_rules)
    ]

    # Filter out the True (finds) = 1 (0 would be False)
    output = list(filter(lambda x: x[1], finds))
    # Remove the True tags and just present a list of the unique categories
    output = list(set([x[0] for x in output]))

    return output

# Rule book (quick) scanner function
def kwic_rule_book_scan(rules, docs): 

    # Transform columns to regular expression. 
    rules["keyword"] = [x.replace("*", "[a-zA-Z'-]*") + r"\b" for x in rules["keyword"]]
    rules["rules_pre"] = [translate_to_regex(x) for x in rules["rules_pre"]]
    rules["rules_post"] = [translate_to_regex(x) for x in rules["rules_post"]]
    rules["rules_all"] = [translate_to_regex(x) for x in rules["rules_all"]]
    rules["voids"] = [translate_to_regex(x) for x in rules["voids"]]

    # Clean all texts from request
    categories = [categorize_text(doc, rules, window = 12) for doc in docs]

    return (categories)

# Rule book (syn) scanner function
def rule_book_scan(incidents, syn_dict, rules, run_rules='All', verbose=False):
    
    time_start = datetime.now()
    
    finds_pats = []
    incid_nums = []
    incid_cats = []
    
    # Run all rules or selected rules?
    if run_rules == 'All':
        run_rules_list = range(0, len(rules), 1)
    else:
        # Subtract 1 from each element in list for indices
        for i in range(len(run_rules)):
            run_rules[i] = run_rules[i] - 1
        run_rules_list = run_rules

    finds_count = 0

    for r in run_rules_list:
                
        rul_syns = tokenize(re.sub(r", ", " ", rules.syns[r]))
        
        pos_1st = syn_dict.get(rul_syns[0])
        pos_2nd = syn_dict.get(rul_syns[1])

        if len(rul_syns)==3:
            pos_3rd = syn_dict.get(rul_syns[2])
            syn_count = 3
        else:    
            syn_count = 2
     
        # Connections between synonyms 1-2, 2-3
        connect = ['(.*)', '(.*)']

        # Shuffle rules
        srs = ([1, 0, 2], [0, 2, 1])

        cat = rules.rule[r]
        
        span = rules.span[r]
        
        shuffle = rules.shuffle[r]
        
        voids = rules.voids[r]
     
        search_keyword = rules.keyword[r]

        def add_and_next():
            finds_pats.append(pattern)
            incid_nums.append(irn)
            incid_cats.append(cat)

        console_str = f'Checking rule {r+1} of {len(rules)} ({cat})'
        print(console_str)
        print('='*len(console_str))
        #for row in tqdm(range(len(incidents))):
        
        for row in range(len(incidents)):
            
            sys.stdout.write('\r')
            # the exact output you're looking for:
            per_found = round(100*finds_count/len(incidents), 1)
            timer_now = datetime.now()
            diff_time = f'{round(((timer_now - time_start).seconds)/(60*60), 2)} hrs'
            curr_rown = row+1
            total_ros = len(incidents)
            per_throu = round(100*curr_rown/total_ros, 1)
            outpt_str = f'{curr_rown:,}/{total_ros:,} [{finds_count:,}] {diff_time} {per_found}% classified ({per_throu}% through)...'
            sys.stdout.write(outpt_str)
            sys.stdout.flush()
            
            flag = False
            par_text = incidents.text[row].lower()
            # Check sentence by sentence, don't use span
            # TODO: Check impact of using span, should it be used or not?
            sen_toks = sent_tokenize(par_text)    
            irn = incidents.incident_id[row]
            for chk_text in sen_toks:
                if flag == True: break
                # TODO: remove plurals, workers or worker's >>> worker
                for first_syn in pos_1st:
                    locals()["first_syn"] = first_syn.strip()
                    if flag == True: break
                    for second_syn in pos_2nd: 
                        if flag == True: break
                        
                        if syn_count == 3: 
                            for third_syn in pos_3rd:  
                                if search_keyword == '-':
                                    x = f'{first_syn.strip()}{connect[0]}{second_syn.strip()}{connect[1]}{third_syn.strip()}'
                                    pattern = f'({x})'
                                    check = check_presence(pattern, chk_text)
                                    
                                    if isNaN(voids):
                                        void_check = False
                                    else:    
                                        for void in voids.split(sep = ', '):
                                            void_check = check_presence(f'\\b{void}', chk_text)
                                            if void_check: break
                                    
                                    if check and not void_check: 
                                        if verbose: 
                                            print(f'\n{check}: {pattern}')
                                            print('Goto: Next rule...')
                                        add_and_next()    
                                        finds_count+=1
                                        flag = True                                
                                        break
                                        
                                    else:
                                        for sr in srs:
                                            if len(sr) == 0: continue
                                            a = x.split(sep = connect[0])
                                            if shuffle == False or syn_count != 3:
                                                break
                                            # Adjust the word sequence using shuffle rule                             
                                            pattern = f'({a[sr[0]]}{connect[0]}{a[sr[1]]}{connect[1]}{a[sr[2]]})'
                                            rev_check = check_presence(pattern, chk_text)
                                            
                                            if isNaN(voids):
                                                void_check = False
                                            else:    
                                                for void in voids.split(sep = ', '):
                                                    void_check = check_presence(void, chk_text)
                                                    if void_check: break
                                                                
                                            if rev_check and not void_check:
                                                if verbose: 
                                                    print(f'\n{rev_check}: {pattern} ---Shuffled')
                                                    print('Goto: Next rule...')
                                                finds_count+=1
                                                add_and_next()  
                                                flag = True                                                               
                                                break
                                    
                                else:
                                    test_tokens = tokenize(chk_text)
                                    kwics = get_matches(search_keyword, test_tokens, span)

                                    for kwic in kwics:
                                        if syn_count == 3:
                                            x = f'{first_syn.strip()}{connect[0]}{second_syn.strip()}{connect[1]}{third_syn.strip()}'
                                        else:
                                            x = f'{first_syn.strip()}{connect[0]}{second_syn.strip()}'
                                        pattern = f'({x})'
                                        check = check_presence(pattern, kwic)
                                        
                                        if isNaN(voids):
                                            void_check = False
                                        else:    
                                            for void in voids.split(sep = ', '):
                                                void_check = check_presence(void, chk_text)
                                                if void_check: break
                                        
                                        if check and not void_check: 
                                            if verbose:
                                                print(f'\n{rev_check}: {pattern}')
                                                print('Goto: Next rule...')
                                            finds_count+=1
                                            add_and_next()      
                                            flag = True                             
                                            break

                                        else:
                                            for sr in srs:
                                                if len(sr) == 0: continue
                                                a = x.split(sep = connect[0])
                                                if shuffle == False or syn_count != 3:
                                                    break
                                                # Adjust the word sequence using shuffle rule                                            
                                                pattern = f'({a[sr[0]]}{connect[0]}{a[sr[1]]}{connect[1]}{a[sr[2]]})'
                                                rev_check = check_presence(pattern, chk_text)
                                                
                                                if isNaN(voids):
                                                    void_check = False
                                                else:    
                                                    for void in voids.split(sep = ', '):
                                                        void_check = check_presence(void, chk_text)
                                                        if void_check: break
                                                
                                                if rev_check and not void_check:  
                                                    if verbose: 
                                                        print(f'\n{rev_check}: {pattern} ---Shuffled')
                                                        print('Goto: Next rule...')
                                                    finds_count+=1
                                                    add_and_next()  
                                                    flag = True                                 
                                                    break
                        # Perform two synonym scan
                        else:
                            if search_keyword == '-':
                                x = f'{first_syn.strip()}{connect[0]}{second_syn.strip()}'    
                                pattern = f'({x})'
                                check = check_presence(pattern, chk_text)
                                
                                if isNaN(voids):
                                    void_check = False
                                else:    
                                    for void in voids.split(sep = ', '):
                                        void_check = check_presence(f'\\b{void}', chk_text)
                                        if void_check: break
                                
                                if check and not void_check: 
                                    if verbose: 
                                        print(f'\n{check}: {pattern}')
                                        print('Goto: Next rule...')
                                    add_and_next()    
                                    finds_count+=1
                                    flag = True                                
                                    break
                                    
                                else:
                                    for sr in srs:
                                        if len(sr) == 0: continue
                                        a = x.split(sep = connect[0])
                                        if shuffle == False or syn_count != 3:
                                                break
                                        # Adjust the word sequence using shuffle rule                             
                                        pattern = f'({a[sr[0]]}{connect[0]}{a[sr[1]]}{connect[1]}{a[sr[2]]})'
                                        rev_check = check_presence(pattern, chk_text)
                                        
                                        if isNaN(voids):
                                            void_check = False
                                        else:    
                                            for void in voids.split(sep = ', '):
                                                void_check = check_presence(void, chk_text)
                                                if void_check: break
                                                            
                                        if rev_check and not void_check:
                                            if verbose: 
                                                print(f'\n{rev_check}: {pattern} ---Shuffled')
                                                print('Goto: Next rule...')
                                            finds_count+=1
                                            add_and_next()  
                                            flag = True                                                               
                                            break
                                
                            else:
                                test_tokens = tokenize(chk_text)
                                kwics = get_matches(search_keyword, test_tokens, span)

                                for kwic in kwics:
                                    x = f'{first_syn.strip()}{connect[0]}{second_syn.strip()}'
                                    pattern = f'({x})'
                                    check = check_presence(pattern, kwic)
                                    
                                    if isNaN(voids):
                                        void_check = False
                                    else:    
                                        for void in voids.split(sep = ', '):
                                            void_check = check_presence(void, chk_text)
                                            if void_check: break
                                    
                                    if check and not void_check: 
                                        if verbose:
                                            print(f'\n{rev_check}: {pattern}')
                                            print('Goto: Next rule...')
                                        finds_count+=1
                                        add_and_next()      
                                        flag = True                             
                                        break

                                    else:
                                        for sr in srs:
                                            if len(sr) == 0: continue
                                            a = x.split(sep = connect[0])
                                            if shuffle == False or syn_count != 3:
                                                break
                                            # Adjust the word sequence using shuffle rule                                            
                                            pattern = f'({a[sr[0]]}{connect[0]}{a[sr[1]]}{connect[1]}{a[sr[2]]})'
                                            rev_check = check_presence(pattern, chk_text)
                                            
                                            if isNaN(voids):
                                                void_check = False
                                            else:    
                                                for void in voids.split(sep = ', '):
                                                    void_check = check_presence(void, chk_text)
                                                    if void_check: break
                                            
                                            if rev_check and not void_check:  
                                                if verbose: 
                                                    print(f'\n{rev_check}: {pattern} ---Shuffled')
                                                    print('Goto: Next rule...')
                                                finds_count+=1
                                                add_and_next()  
                                                flag = True                                 
                                                break
                                            
        print('\n')
    out_df = pd.DataFrame(data=incid_nums, columns=['incid_nums'])
    out_df['finds_pats'] = finds_pats
    out_df['incid_cats'] = incid_cats
    return(out_df)


def deepdive_results(dat, incidents_df, finds_df, focus='finds'):
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