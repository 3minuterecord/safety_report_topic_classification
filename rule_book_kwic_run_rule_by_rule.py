import pandas as pd
import rule_book_functs as rbfuncts
from tqdm.notebook import tqdm
from datetime import datetime

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
        docs = incidents

        # Load the synonym database
        syns_data = pd.read_csv('synonyms.csv')
        syns_data['syn'] = syns_data['syn'].apply(rbfuncts.replace_syns)

        # Get categories
        rules_to_run = rul_csv.group.unique()
        
        # Open a log file for results        
        # Current date and time for referencing filename
        now = datetime.now() 
        date_time = now.strftime("%y%m%d%H%M%S") 
        log_file = open(f'output/{date_time}_log.txt', 'w')
        
        for rule_to_run in rules_to_run:
        #rule_to_run = 'general injury'
                print(f'Scanning for rule: "{rule_to_run}"')
                categories = rbfuncts.kwic_rule_book_scan(rules=rul_csv, docs=docs["text"], syns_db=syns_data, run_rules=rule_to_run, verb=False)

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

                unclassified_count = len(out_df.loc[(out_df.category == '*** Not Classified')])
                classified_count = len(out_df) - unclassified_count
                classified_count = "{:,}".format(classified_count)
                classified_percent = round(100 - round(100*(unclassified_count / len(out_df)), 1))

                out_df.to_csv(f'output/{rule_to_run}_{classified_count}_out_df_temp.csv')
                print('\n')
                
                final_str = f' Total classified: {classified_percent}% ({classified_count})'
                print('+'+'-'*(len(final_str)-1)+'+')
                print(final_str)
                print('+'+'-'*(len(final_str)-1)+'+')
                print('\n')

                # Write output in latex format for copy + paste into report (for tabulated results)
                write_str = f'\t{rule_to_run} & {classified_count} & {classified_percent}\\'
                log_file.write("%s\n" % write_str)
                
        log_file.close() 
        
if __name__ == "__main__":
        main()