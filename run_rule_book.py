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
incidents_fn = "data/source/20220413_D1_Incidents.csv"
incidents = pd.read_csv(incidents_fn, dtype=str)

# Concatenate some of the fields to make the 'text' field for searching
incidents.rename(columns={'IncidentNumber': 'incident_id'}, inplace=True)
incidents['text'] = (
        incidents['ShortDescription'].astype(str).fillna('') + ' ' + 
        incidents['FullDescription'].astype(str).fillna('') + ' ' + 
        incidents['ImmediateAction'].astype(str).fillna('')
).str.lower()

# We only need the incident ID and the text for now
incidents = incidents[['incident_id', 'text']]

# Now load the synonym dictionary in its raw csv format
syn_csv = pd.read_csv('synonyms.csv')

# Now convert the csv format into a dictionary of synonyms
syn_dict = {}
for r in range(len(syn_csv)):
    syn_toks = syn_csv.keywords[r].split(',')
    syn_dict.update({syn_csv.syn[r]:syn_toks})
    
# Now load the rule definitions
rul_csv = pd.read_csv('rules.csv')

# Now run some quick tests
txt = 'This is me. He tripped and fell from the ladder and dtep-sadder.'
tdf = pd.DataFrame({'incident_id':[1052], 'text':[txt]})
rbfuncts.rule_book_scan(tdf, syn_dict, rul_csv)

