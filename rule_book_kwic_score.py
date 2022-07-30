from cgitb import reset
import pandas as pd
import rule_book_functs as rbfuncts
from tqdm.notebook import tqdm
import time

# Description:
# +--------------------------------------------------------------------+
# 1. Load raw incident data, concatenate & remove unused fields
# 2. Load rule book definitions
# 3. Run rule book function based on 'kwic' & synonyms to classify text
# +--------------------------------------------------------------------+

def main():
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

        # Load the synonym database
        syns_data = pd.read_csv('synonyms.csv')
        syns_data['syn'] = syns_data['syn'].apply(rbfuncts.replace_syns)

        # Create the sample without replacement
        print('\n')
        sample_size = int(input('Sample size: '))
        classified_count = 0
        sample_amp_factor = 1.5
        #while classified_count < sample_size:
        for i in range(10):
                sample_for_test = incidents.sample(int(sample_size*sample_amp_factor))
                sample_for_test.reset_index(inplace=True)
                print(sample_for_test)
                categories = rbfuncts.kwic_rule_book_scan(
                        rules=rul_csv, 
                        docs=sample_for_test["text"], syns_db=syns_data, run_rules='all', verb=False
                )
                
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
                out_df['text'] = sample_for_test['text'].tolist()
                out_df['dset'] = sample_for_test['dataset'].tolist()

                unclassified_count = len(out_df.loc[(out_df.category == '*** Not Classified')])
                check_count = len(out_df) - unclassified_count   
                print('Checking Classified count: ', check_count)
                classified_count = check_count
                if classified_count >= sample_size:
                        break
                sample_amp_factor = 1.1 * sample_amp_factor
                print('Try again...')
        
        print('**** classified count: ', classified_count)
        out_df = out_df.loc[(out_df.category != '*** Not Classified')]
        out_df.reset_index(inplace=True)
        out_df = out_df.iloc[0:sample_size,]
        print('Output no. of rows: ', len(out_df))
                
        scores = []
        for r, doc in enumerate(out_df["text"]):
                print('\n')
                cat_title = f'{r+1}: {out_df.category[r]}'
                print(cat_title)
                print('='*len(cat_title))
                print(doc)
                print('\n')
                score = int(input('Score (1: Good, 2: Fair, 3: Poor): '))
                scores.append(score)
        out_df['scores'] = scores
        
        print('Writing scores...')
        datetime_now = time.time()
        out_df.to_csv(f'scores/{datetime_now}_{classified_count}_sample_scores.csv')
        print('done \n')
        
        print(scores)
       
        
if __name__ == "__main__":
        main()