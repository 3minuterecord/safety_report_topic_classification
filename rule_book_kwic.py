from unicodedata import category
import pandas as pd
import rule_book_functs as rbfuncts

# Description:
# +--------------------------------------------------------------------+
# 1. Load raw incident data, concatenate & remove unused fields
# 2. Load rule book definitions
# 3. Run rule book function to classify text
# +--------------------------------------------------------------------+

# Load raw incident data
incidents = pd.read_csv("data/source/20220413_D1_Incidents.csv", dtype=str)  

# Load the 'kwic' rule definitions
# 'kwic' = Keyword in context
rul_csv = pd.read_csv('data/rule_book_kwic.csv')

# Concatenate some of the fields to make the 'text' field for searching
incidents.rename(columns={'IncidentNumber': 'incident_id'}, inplace=True)
incidents['text'] = (
        incidents['ShortDescription'].astype(str).fillna('') + ' ' + 
        incidents['FullDescription'].astype(str).fillna('') + ' ' + 
        incidents['ImmediateAction'].astype(str).fillna('')
).str.lower()

# We only need the incident ID and the text for now
incidents = incidents[['incident_id', 'text']]

# Run on sample of 100 incidents
# Run on last or create new (run on last to improve rules)
run_choice = input('Run fresh sample (y/n):')
if run_choice == 'y':
      sample100 = incidents.sample(100)
      sample100.to_csv('temp_sample.csv')
      docs = sample100  
else:
      docs = pd.read_csv('temp_sample.csv')        

# Load the synonym database
syns_data = pd.read_csv('synonyms.csv')
syns_data['syn'] = syns_data['syn'].apply(rbfuncts.replace_syns)

# Get categories
categories = rbfuncts.kwic_rule_book_scan(rules=rul_csv, docs=docs["text"], syns_db=syns_data)

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

# Print to console in a review-friendly manner
for r in range(len(out_df)):
        print(out_df.category[r])
        print('='*len(out_df.category[r]))
        print(out_df.text[r])
        print('\n')

unclassified_count = len(out_df.loc[(out_df.category == '*** Not Classified')])
classified_percent = 100 - round(100*(unclassified_count / len(out_df)), 1)

print('+------------------------+')
print(f' Total classified: {classified_percent}%')
print('+------------------------+')
print('\n')