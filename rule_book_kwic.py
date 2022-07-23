from unicodedata import category
import pandas as pd
import rule_book_functs as rbfuncts

# Description:
# +--------------------------------------------------------------------+
# 1. Load raw incident data, concatenate & remove unused fields
# 2. Load rule book definitions
# 3. Run rule book function based on 'kwic' & synonyms to classify text
# +--------------------------------------------------------------------+

# Load raw incident data
req_cols1 = ['IncidentNumber', 'ShortDescription', 'FullDescription', 'ImmediateAction']
req_cols2 = ['ID', 'EventTitle', 'Final Narrative']
incidents = pd.read_csv("data/source/20220413_D1_Incidents.csv", dtype=str, usecols=req_cols1)  
osha_incs = pd.read_csv("data/source/OSHA_January2015toJuly2021.csv", dtype=str, usecols=req_cols2)  

# Load the 'kwic' rule definitions
# 'kwic' = Keyword in context
rul_csv = pd.read_csv('data/rule_book_kwic.csv')

# Some clean up for Wood dataset
# Concatenate some of the fields to make the 'text' field for searching
incidents.rename(columns={'IncidentNumber': 'incident_id'}, inplace=True)
incidents['text'] = (
        incidents['ShortDescription'].astype(str).fillna('') + ' ' + 
        incidents['FullDescription'].astype(str).fillna('') + ' ' + 
        incidents['ImmediateAction'].astype(str).fillna('')
).str.lower()
incidents['dataset'] = 'ORGP'

# We only need the incident ID and the text for now
incidents = incidents[['incident_id', 'dataset', 'text']]

# Some clean up for OSHA dataset
# Concatenate some of the fields to make the 'text' field for searching
osha_incs.rename(columns={'ID': 'incident_id'}, inplace=True)
osha_incs['text'] = (
        osha_incs['EventTitle'].astype(str).fillna('') + ' ' + 
        osha_incs['Final Narrative'].astype(str).fillna('')
).str.lower()
osha_incs['dataset'] = 'OSHA'

# We only need the incident ID and the text for now
osha_incs = osha_incs[['incident_id', 'dataset', 'text']]

# Combine OSHA and Wood datasets
incidents = pd.concat([incidents, osha_incs])

run_choice = input('Run on sample or all data? (s/a): ')

if run_choice == 's':
        # Run on sample of 100 incidents
        # Run on last or create new (run on last to improve rules)
        sample_choice = input('Run fresh sample (y/n):')
        if sample_choice == 'y':
                sample100 = incidents.sample(100)
                sample100.to_csv('temp_sample.csv')
                docs = sample100  
        else:
                docs = pd.read_csv('temp_sample.csv')        
else:
       docs = incidents

# Load the synonym database
syns_data = pd.read_csv('synonyms.csv')
syns_data['syn'] = syns_data['syn'].apply(rbfuncts.replace_syns)

# Get categories
rule_extent = input("Run all rules (state: 'all') or selected rule (e.g., state: 'slips & trips'): ")
categories = rbfuncts.kwic_rule_book_scan(rules=rul_csv, docs=docs["text"], syns_db=syns_data, run_rules=rule_extent)

# Now tidy up the presentation of the output for printing
# This will help with analysis/review of classifications and improvements to rule-book
cats = []
for entry in categories:
        if ', '.join(entry) == '':
                cats.append('*** Not Classified') # So as to easily identify unclassified texts
        else:                
                cats.append(', '.join(entry))

# Convert to a simple datafrae
out_df = pd.DataFrame(cats, columns=['category'])
out_df['text'] = docs['text'].tolist()
out_df['dset'] = docs['dataset'].tolist()

if run_choice == 'a':
        out_df.to_csv('out_df_temp.csv')
        print('\n')
else:
        # Print to console in a review-friendly manner
        print('\n')
        for r in range(len(out_df)):
                print(out_df.category[r])
                print('='*len(out_df.category[r]))
                print(out_df.text[r])
                print('~ ' + out_df.dset[r])
                print('\n')

unclassified_count = len(out_df.loc[(out_df.category == '*** Not Classified')])
classified_count = len(out_df) - unclassified_count
classified_percent = round(100 - round(100*(unclassified_count / len(out_df)), 1), 1)

final_str = f' Total classified: {classified_percent}% ({classified_count})'
print('+'+'-'*(len(final_str)-1)+'+')
print(final_str)
print('+'+'-'*(len(final_str)-1)+'+')
print('\n')