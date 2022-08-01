from cgitb import reset
import pandas as pd
import rule_book_functs as rbfuncts
from datetime import datetime
import numpy as np

# Description:
# +--------------------------------------------------------------------+
# 1. Load raw incident data, concatenate & remove unused fields
# 2. Load rule book definitions
# 3. Apply rule book based on 'kwic' & synonyms to classify text
# 4. Save sample of classified texts for scoring
# +--------------------------------------------------------------------+

def main():       
        # Load raw incident data
        req_cols1 = ['IncidentNumber', 'ShortDescription', 'FullDescription', 'ImmediateAction']
        req_cols2 = ['ID', 'EventTitle', 'Final Narrative']
        req_cols3 = ['text']
        incidents = pd.read_csv("data/source/20220413_D1_Incidents.csv", dtype=str, usecols=req_cols1)  
        osha_incs = pd.read_csv("data/source/OSHA_January2015toJuly2021.csv", dtype=str, usecols=req_cols2)  
        manu_fabr = pd.read_csv("data/source/manually_fabricated.csv", dtype=str, usecols=req_cols3)  
        
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

        # Add identifier fields to the manually fabricated dataset
        manu_fabr['dataset'] = 'MANF'
        manu_fabr['text'] = manu_fabr['text'].str.lower()
        manu_fabr['incident_id'] = [i+1 for i in range(len(manu_fabr))]
     
        # Load the synonym database
        syns_data = pd.read_csv('synonyms.csv')
        syns_data['syn'] = syns_data['syn'].apply(rbfuncts.replace_syns)

        # Create the sample without replacement
        print('\n')
        sample_size = int(input('Sample size: '))
        
        # TODO - Make this automatic, user should not have think up the splits
        # Specify splits (i.e., how many to sample from each dataset)
        sample_splits = input("Splits ('wood, osha, fabs'): ")
        sample_splits = sample_splits.split(', ')
        classified_count = 0
        for i in range(10):
                # Randomly sample from each dataset so we have some
                # representation from each
                sample_1 = incidents.sample(int(sample_splits[0]))
                sample_2 = osha_incs.sample(int(sample_splits[1]))
                sample_3 = manu_fabr.sample(int(sample_splits[2]))
                
                # Combine all three (3) sample datasets
                sample_df = pd.concat([sample_1, sample_2, sample_3])
                
                #sample_df = incidents.sample(int(sample_size*sample_amp_factor))
                categories = rbfuncts.kwic_rule_book_scan(
                        rules=rul_csv, 
                        docs=sample_df["text"], syns_db=syns_data, run_rules='all', verb=False
                )
                
                # Now tidy up the presentation of the output for printing
                cats = []
                for entry in categories:
                        if ', '.join(entry) == '':
                                cats.append('*** Not Classified') # So as to easily identify unclassified texts
                        else:                
                                cats.append(', '.join(entry))

                # Convert to a simple datafrae
                out_df = pd.DataFrame(cats, columns=['category'])
                out_df['text'] = sample_df['text'].tolist()
                out_df['dset'] = sample_df['dataset'].tolist()

                unclassified_count = len(out_df.loc[(out_df.category == '*** Not Classified')])
                check_count = len(out_df) - unclassified_count   
                print('Checking Classified count: ', check_count)
                classified_count = check_count
                if classified_count >= sample_size:
                        break
                sample_amp_factor = 1.1 * sample_amp_factor
                print('Try again...')
        
        out_df = out_df.loc[(out_df.category != '*** Not Classified')]
        out_df = out_df.sample(sample_size)
        #out_df = out_df.iloc[0:sample_size,]
        out_row_count = len(out_df)
        print('Output no. of rows: ', out_row_count)
        
        # current date and time
        now = datetime.now() 
        date_time = now.strftime("%y%m%d%H%M%S")
        
        print('Writing data for testing...')
        out_df.to_csv(f'test_samples/{date_time}_{sample_size}_sample_scores.csv', index=False)
        print('done \n')
        
if __name__ == "__main__":
        main()