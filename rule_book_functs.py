import numpy as np
import pandas as pd
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
from nltk.stem import PorterStemmer as stemmer
from tqdm.notebook import tqdm
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

def translate_to_regex_simple(rule_part):
    """
    converts rule_book rules to regex format;
    drops trailing separators in process
    """
    if isinstance(rule_part, str): # If rule part is a string...
        rule_part = re.sub(r"\s{2,}", " ", rule_part)
        rule_part = re.sub(r'\\\\b', r'\\b', rule_part)
        
        return r'(\b' + r'\b)|(\b'.join([s for s in rule_part.split('_ ') if s]) + r'\b)'
    else:
        return ''
 
def mutate_syn(syns, syns_db, rule, num):
    syn_rules = []
    if num == 1:    
        syn_raw = syns[0]
        syn = re.sub(r"[\([{})\]]", '', syn_raw)
        found_syn = syns_db.loc[(syns_db['syn'] == syn)]
        for keyword in found_syn.iloc[0, 1].split(', '):
            syn_rules.append(re.sub(syn_raw, keyword, rule))
        syn_rules = '_ '.join(syn_rules)
        return(syn_rules)
    elif num == 2:
        syn_raw_1 = syns[0]
        syn_1 = re.sub(r"[\([{})\]]", '', syn_raw_1)
        found_syn_1 = syns_db.loc[(syns_db['syn'] == syn_1)]

        syn_raw_2 = syns[1]
        syn_2 = re.sub(r"[\([{})\]]", '', syn_raw_2)
        found_syn_2 = syns_db.loc[(syns_db['syn'] == syn_2)]

        for keyword_1 in found_syn_1.iloc[0, 1].split(', '):
            for keyword_2 in found_syn_2.iloc[0, 1].split(', '):
                pass_1 = re.sub(syn_raw_1, keyword_1, rule)
                pass_2 = re.sub(syn_raw_2, keyword_2, pass_1)
                syn_rules.append(pass_2)
        syn_rules = '_ '.join(syn_rules)
        return(syn_rules)
    elif num == 3:
        syn_raw_1 = syns[0]
        syn_1 = re.sub(r"[\([{})\]]", '', syn_raw_1)
        found_syn_1 = syns_db.loc[(syns_db['syn'] == syn_1)]

        syn_raw_2 = syns[1]
        syn_2 = re.sub(r"[\([{})\]]", '', syn_raw_2)
        found_syn_2 = syns_db.loc[(syns_db['syn'] == syn_2)]

        syn_raw_3 = syns[2]
        syn_3 = re.sub(r"[\([{})\]]", '', syn_raw_3)
        found_syn_3 = syns_db.loc[(syns_db['syn'] == syn_3)]

        for keyword_1 in found_syn_1.iloc[0, 1].split(', '):
            for keyword_2 in found_syn_2.iloc[0, 1].split(', '):
                for keyword_3 in found_syn_3.iloc[0, 1].split(', '):
                    pass_1 = re.sub(syn_raw_1, keyword_1, rule)
                    pass_2 = re.sub(syn_raw_2, keyword_2, pass_1)
                    pass_3 = re.sub(syn_raw_3, keyword_3, pass_2)
                    syn_rules.append(pass_3)
        syn_rules = '_ '.join(syn_rules)
        return(syn_rules)    
 
 
def translate_to_regex(rule_part, syns_db):
    """
    converts rule_book rules to regex format;
    drops trailing separators in process
    performs preprocessing to mutate synonyms & expand rule set for all permutations
    """
    if isinstance(rule_part, str): # If rule part is a string...
        
        # 1st, we need to preprocess and mutate synonyms if they are found in rules
        # 1st step is to split the rule set into individual rules
        split_rule = rule_part.split('_ ')
        # create an empty list to hold the mutates rule set
        out_rule = []

        for rule in split_rule:
            # Check for presence of synonym, e.g., {eye}
            syns = re.findall("{[a-zA-Z'-]*}", rule)
            # How many do we find?
            syn_count = len(syns)
            # No process based on how many we find (max number is 3, min is 0)
            if syn_count == 1:
                syn_rules = mutate_syn(syns, syns_db, rule, 1)
                out_rule.append(syn_rules)
            elif syn_count == 2:                
                syn_rules = mutate_syn(syns, syns_db, rule, 2)
                out_rule.append(syn_rules)
            # elif syn_count == 3:                
            #     syn_rules = mutate_syn(syns, syns_db, rule, 3)
            #     out_rule.append(syn_rules)
            else:       
                # Do nothin, no mutation required as no synonym has been specified
                out_rule.append(rule)
                
        # Join back to single rule set        
        out_rule = '_ '.join(out_rule)
        
        # Now translate to regex
        rule_part = re.sub(r"\s{2,}", " ", out_rule)
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

# Function to flatten a list of lists
# [[1, 2], [1, 2, 3]] >> [1, 2, 1, 2, 3]
def flatten(list_of_lists):
    return [x for xs in list_of_lists for x in xs]

def check_apply(sen, rules):
    if len(rules) != 0:
        df_scan = pd.DataFrame(rules.split('|'), columns=['pattern'])    
        df_scan['doc'] = sen
        df_scan['finds'] = df_scan[['pattern', 'doc']].apply(lambda x: check_presence(*x), axis=1)    
        find = bool(sum(df_scan['finds']))       
    else:
        find = False   
    return(find)

def check_apply_all(sens_pre, sens_post, sens_all, check_pre, check_post, check_all, check_void):
    pre_check, post_check, all_check, void_check = False, False, False, False
    for sen in sens_pre:        
        if len(check_pre) != 0:
            pre_check = check_apply(sen, check_pre) or pre_check
            if pre_check: break
            
    for sen in sens_post:      
        if len(check_post) != 0:
            post_check = check_apply(sen, check_post) or post_check
            if post_check: break 
            
    for sen in sens_all:             
        if len(check_all) != 0:
            all_check = check_apply(sen, check_all) or all_check
            #print('check 1: ', check_apply(sen, check_all))
            #print('check 2: ', all_check)
            if all_check: break 
        if len(check_void) != 0:
            void_check = check_apply(sen, check_void)   
            if void_check: break 

    final_match = (pre_check or post_check or all_check) and not void_check
        
    return(final_match)

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
    
    # Remove any slashes
    doc = doc.replace('/', ' ')
    doc = doc.replace(' / ', ' ')
    doc = doc.lower()
    
    # Break the text into sentences
    # Each sentence is checked separately
    sen_toks = sent_tokenize(doc)
    
    # If there is no keyword it will be flagged as '-'
    # In this case, we just check each sentence for the rule set
    if keyword == '-\\b':
        void = False   
        for all_ in sen_toks:
            # Very long rule patterns run very slowly, the following method using 
            # dataframe and an apply function performs significantly better but
            # TODO - there is still room for optimisation
            df_scan = pd.DataFrame(check_all.split('|'), columns=['pattern'])    
            df_scan['doc'] = all_
            df_scan['finds'] = df_scan[['pattern', 'doc']].apply(lambda x: check_presence(*x), axis=1)   
            # Alternative approach not used as a bit slower than above during tests... 
            #df_scan['finds'] = df_scan.apply(lambda x: check_presence(x.pattern, x.doc), axis=1)
            find = bool(sum(df_scan['finds']))
            if len(check_void) != 0:
                df_void = pd.DataFrame(check_void.split('|'), columns=['pattern'])
                df_void['doc'] = all_
                df_void['voids'] = df_void[['pattern', 'doc']].apply(lambda x: check_presence(*x), axis=1)
                void = bool(sum(df_void['voids']))
            final_match = find and not void    
            if final_match: break
 
    else:                
        # Remove any whitespace
        keyword = keyword.strip()    
        
        # Check if keyword is in sentence
        any_match = re.search(keyword, doc)

        if any_match is None:
            return False
        else:
            # We want to finad and extract the context of the keyword in the sentence
            # With a predefined window
            pre_context = "(?:[a-zA-Z'-]+[^a-zA-Z'-]+){0,<window>}<keyword>".replace('<keyword>', str(keyword)).replace('<window>', str(window))
            post_context = "<keyword>(?:[^a-zA-Z'-]+[a-zA-Z'-]+){0,<window>}".replace('<keyword>', str(keyword)).replace('<window>', str(window))
            all_context = "(?:[a-zA-Z'-]+[^a-zA-Z'-]+){0,<window>}<keyword>(?:[^a-zA-Z'-]+[a-zA-Z'-]+){0,<window>}".replace('<keyword>', str(keyword)).replace('<window>', str(window))
            
            # Check each sentence and extract each context from each sentence
            # This could produce list of lists, hence we need to flatten.
            pre_match = flatten([re.findall(pre_context, t) for t in sen_toks]) 
            post_match = flatten([re.findall(post_context, t) for t in sen_toks])
            all_match = flatten([re.findall(all_context, t) for t in sen_toks])
            # print(all_match)

        # Perform final tests
        #final_match = (pre_check or post_check or all_check) and not void_check
        
        final_match = check_apply_all(
            sens_pre=pre_match, 
            sens_post=post_match, 
            sens_all=all_match, 
            check_pre=check_pre, 
            check_post=check_post, 
            check_all=check_all, 
            check_void=check_void
            )
        
    return final_match

# Function to categorize text using simple find pattern approach
def categorize_text(doc, rules, focus_group, window=5, verbose=False):
    """
    to each text (list of tokens) in a df assigns incident categories based on rules from rules df
    can assign several categories or none at all
    :param text_df: dataframe with a mandatory column "tokens" - list of strings, result of text tokenization
    :param rules: dataframe with rules (rule_book file)
    :param window: how may words to consider context
    :return: None, adds "categories" column to text_df, where categories are stored as concatenated strings
    """
       
    if focus_group != 'all':
        rules = rules.loc[(rules['group'] == focus_group)]
        rules.reset_index(drop=True, inplace=True)
   
    if len(rules) == 0:
        sys.exit(f"Error: '{focus_group}' is not a recogised rule...")
            
    # Category indicators are stored in a bool array (n_texts, n_cats)
    # which is updated as the rules are checked
    categories = list(set(rules["group"])) # Use set to remove duplicate groups (each group can have > 1 rule)

    cat_dict = {cat: i for i, cat in enumerate(categories)}
    category_indicators = [False] * len(categories)

    num_rules = len(rules['group'])

    for i in range(num_rules):            
        group_name = rules["group"][i]
        group_name_len = len(group_name)
        max_group_name_len = 39
        print_name = group_name + ' ' + '-'*(max_group_name_len - group_name_len - 1)
        if verbose: print(print_name, end = '\r', flush=True)
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

    # Check doc for each rule in the rule book
    # Create list of Group, Bool, e.g., ['Slips & Trips', True]
    finds = [
        (
            rules['group'][j],
            # Find pattern returns the result of the complete context check
            # Applying pre, post, all and void checks
            # Returns true if rule checks out for doc/text
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

# Function to replace unused text in synonym dictionary keywords
def replace_syns(in_str):
    mod_str = re.sub('_syns', '', in_str) 
    return(mod_str)

# Rule book (kwic) scanner function
# 'kwic' = keyword in context
def kwic_rule_book_scan(rules, docs, syns_db, run_rules='all', verb = False): 

    # Transform columns to regular expression. 
    rules["keyword"] = [x.replace("*", "[a-zA-Z'-]*") + r"\b" for x in rules["keyword"]]
    rules["rules_pre"] = [translate_to_regex(x, syns_db) for x in rules["rules_pre"]]
    rules["rules_post"] = [translate_to_regex(x, syns_db) for x in rules["rules_post"]]
    rules["rules_all"] = [translate_to_regex(x, syns_db) for x in rules["rules_all"]]
    rules["voids"] = [translate_to_regex(x, syns_db) for x in rules["voids"]]
    #rules.to_csv('rules_out_temp.csv')
    # Clean all texts from request
    categories = [categorize_text(doc, rules, window = 12, focus_group=run_rules, verbose=verb) for doc in tqdm(docs)]
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