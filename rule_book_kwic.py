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
rul_csv = pd.read_csv('data/rule_book.csv')

# Concatenate some of the fields to make the 'text' field for searching
incidents.rename(columns={'IncidentNumber': 'incident_id'}, inplace=True)
incidents['text'] = (
        incidents['ShortDescription'].astype(str).fillna('') + ' ' + 
        incidents['FullDescription'].astype(str).fillna('') + ' ' + 
        incidents['ImmediateAction'].astype(str).fillna('')
).str.lower()

# We only need the incident ID and the text for now
incidents = incidents[['incident_id', 'text']]

# Transform columns to regular expression. 
rules=rul_csv
rules["keyword"] = [x.replace("*", "[a-zA-Z'-]*") + r"\b" for x in rules["keyword"]]
rules["rules_pre"] = [rbfuncts.translate_to_regex(x) for x in rules["rules_pre"]]
rules["rules_post"] = [rbfuncts.translate_to_regex(x) for x in rules["rules_post"]]
rules["rules_all"] = [rbfuncts.translate_to_regex(x) for x in rules["rules_all"]]
rules["voids"] = [rbfuncts.translate_to_regex(x) for x in rules["voids"]]

# Clean all texts from request
sample100 = incidents.sample(100)
docs=sample100
categories = [rbfuncts.categorize_text(doc, rules, window = 12) for doc in docs["text"]]
print(categories)
print(len(categories))

# Run on sample of 100 incidents
#sample100 = incidents.sample(100)
#print(sample100)
#test = rbfuncts.quick_rule_book_scan(rules=rul_csv, docs=sample100)
#print(test)