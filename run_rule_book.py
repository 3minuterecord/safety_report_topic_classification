import pandas as pd
import rule_book_functs as rbfuncts

# Description:
# +--------------------------------------------------------------------+
# 1. Load raw incident data, concatenate & remove unused fields
# 2. Load synonym csv and convert required to dictionary format
# 3. Load rule book definitions
# 4. Run rule book function to classify text
# +--------------------------------------------------------------------+

# Load raw incident data
incidents = pd.read_csv("data/source/20220413_D1_Incidents.csv", dtype=str)  

# Load the synonym dictionary in its raw csv format
syn_csv = pd.read_csv('synonyms.csv')

# Load the rule definitions
rul_csv = pd.read_csv('rules.csv')

# Concatenate some of the fields to make the 'text' field for searching
incidents.rename(columns={'IncidentNumber': 'incident_id'}, inplace=True)
incidents['text'] = (
        incidents['ShortDescription'].astype(str).fillna('') + ' ' + 
        incidents['FullDescription'].astype(str).fillna('') + ' ' + 
        incidents['ImmediateAction'].astype(str).fillna('')
).str.lower()

# We only need the incident ID and the text for now
incidents = incidents[['incident_id', 'text']]

# Now convert the csv format into a dictionary of synonyms
syn_dict = {}
for r in range(len(syn_csv)):
    syn_toks = syn_csv.keywords[r].split(',')
    syn_dict.update({syn_csv.syn[r]:syn_toks})

# Now run the rule book
TEST = False
if TEST:
    # Run a quick tests
    txt = 'Spotted when he had no ppe.'
    tdf = pd.DataFrame({'incident_id':[1052], 'text':[txt]})
    finds_df = rbfuncts.rule_book_scan(tdf, syn_dict, rul_csv, verbose=True)
    finds_row_count = len(list(dict.fromkeys(finds_df[finds_df.finds_list == True].incid_nums)))
    print(f'Number of finds is {finds_row_count}')
    print(finds_df)
else:
    # Run on sample of 100 incidents
    sample100 = pd.read_csv('sample100.csv', dtype=str)
    finds_df = rbfuncts.rule_book_scan(sample100, syn_dict, rul_csv, run_rules='All')  
    conso_df = finds_df.groupby(['incid_nums'])['incid_cats'].apply(', '.join).reset_index()
    conso_df['incid_cats'] = conso_df['incid_cats'].apply(lambda x: rbfuncts.remove_dups(x))
    # How many incidents were classified
    finds_row_count = len(conso_df)
    rbfuncts.deepdive_results(sample100, incidents, finds_df, focus='finds')
    print(finds_df)
    print('\n')
    print(f'Number of finds is {finds_row_count}')
    print('\n')
    print(conso_df)
