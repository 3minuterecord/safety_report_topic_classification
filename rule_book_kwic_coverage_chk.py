import pandas as pd
import rule_book_functs as rbfuncts
from datetime import datetime
import numpy as np
from statistics import median

# Description:
# +--------------------------------------------------------------------+
# 1. Load raw incident data, concatenate & remove unused fields
# 2. Load rule book definitions
# 3. Apply rule book based on 'kwic' & synonyms to classify text
# 4. Save sample of classified texts for scoring
# +--------------------------------------------------------------------+

def main():     
        # Create the sample without replacement
        print('\n')
        sample_size = int(input('Sample size: '))
        num_experim = int(input('Number of tests: '))      

        # Open a log file for results        
        # Current date and time for referencing filename
        now = datetime.now() 
        date_time = now.strftime("%y%m%d%H%M%S") 
        log_file = open(f'coverage_checks/{date_time}_log.txt', 'w')  
        
        # Gather coverages in list so average and median is calculated
        coverages = []
        for t in range(num_experim):  
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
                              
                # Combine all three (3) datasets
                #df_all = pd.concat([incidents, osha_incs, manu_fabr])
                df_all = pd.concat([incidents, osha_incs])
                
                # Randomly sample (proportionate sampling) from dataset
                sample_frac = (sample_size/len(df_all))
                
                test_str = f'Test {t+1}'
                print(f'\n{test_str}')
                print('='*len(test_str))
                sample = df_all.groupby('dataset', group_keys=False).apply(lambda x: x.sample(frac=sample_frac))
                categories = rbfuncts.kwic_rule_book_scan(
                        rules=rul_csv, 
                        docs=sample["text"], syns_db=syns_data, run_rules='all', verb=False
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
                out_df['text'] = sample['text'].tolist()
                out_df['dset'] = sample['dataset'].tolist()

                unclassified_count = len(out_df.loc[(out_df.category == '*** Not Classified')])
                check_count = len(out_df) - unclassified_count   
                class_perct = round(100*check_count/sample_size)
                print('Classified count: ', check_count)
                print(f'Classified perct: {class_perct}%')
                
                coverages.append(class_perct)
                
                # Write output in latex format for copy + paste into report (for tabulated results)
                write_str = f'{t+1} & {date_time} & {sample_size} & {class_perct}\\'
                log_file.write("%s\n" % write_str)     
                
                # current date and time
                now = datetime.now() 
                date_time = now.strftime("%y%m%d%H%M%S") 
                
                # Save the output file with classifications for verification/checking                                      
                out_df.to_csv(f'coverage_checks/{date_time}_{sample_size}_{int(class_perct)}_sample_coverage.csv', index=False)                
        
        # Add the average and median coverage to the log file
        write_str = f'Min: {min(coverages)}, average: {rbfuncts.average_lst(coverages)}, median: {median(coverages)}, max: {max(coverages)}'
        log_file.write("%s\n" % write_str) 
        log_file.write("%s\n" % coverages) 
        log_file.close()        
        
if __name__ == "__main__":
        main()