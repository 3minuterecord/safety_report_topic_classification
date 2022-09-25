from unicodedata import category
import pandas as pd
import rule_book_functs as rbfuncts
from tqdm.notebook import tqdm
from io import StringIO

# Description:
# +--------------------------------------------------------------------+
# 1. Load an incident file (small) or enter text of an incident directly
# 2. Load rule book definitions
# 3. Run rule book function based on 'kwic' & synonyms to classify text
# +--------------------------------------------------------------------+

def main():
        
        # Run from file or text:
        run_type = input("Run from file ('f') or text ('t'): ")
        
        if run_type == 't':
                text_in = StringIO(input("Paste text: "))
                docs = pd.DataFrame(text_in, columns = ['text'])
                docs["dset"] = 'ONFY'
                docs_test=docs["text"]                
        else:        
                sample_ref = input("Enter file ref.: ")
                docs = pd.read_csv(f"13_test_samples/{sample_ref}_100_sample_scores.csv", dtype=str)
                docs_test=docs["text"]
        
        # 'kwic' = Keyword in context
        rul_csv = pd.read_csv('01_data/rule_book_kwic.csv')
        
        # Load the synonym database
        syns_data = pd.read_csv('04_rule_book/synonyms.csv')
        syns_data['syn'] = syns_data['syn'].apply(rbfuncts.replace_syns)

        # Get categories
        rule_extent = input("Run all rules (state: 'all') or selected rule (e.g., state: 'slips & trips'): ")
        if rule_extent == 'd':
                topic_groups = set(list(rul_csv.group))
                for group in topic_groups:
                        print('Checking: ', group)
                        categories = rbfuncts.kwic_rule_book_scan(rules=rul_csv, docs=docs_test, syns_db=syns_data, run_rules=group)
        else:        
                categories = rbfuncts.kwic_rule_book_scan(rules=rul_csv, docs=docs_test, syns_db=syns_data, run_rules=rule_extent, verb=False)

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
        out_df['dset'] = docs['dset'].tolist()

        unclassified_count = len(out_df.loc[(out_df.category == '*** Not Classified')])
        classified_count = len(out_df) - unclassified_count
        classified_count = "{:,}".format(classified_count)
        classified_percent = round(100 - round(100*(unclassified_count / len(out_df)), 1), 1)

        out_df.to_csv(f'08_output/{rule_extent}_{classified_count}_out_df_temp.csv')
        
        # Print to console in a review-friendly manner
        print('\n')
        for r in range(len(out_df)):
                cat_title = f'{r+1}: {out_df.category[r]}'
                print(cat_title)
                print('='*len(cat_title))
                print(out_df.text[r])
                print('~ ' + out_df.dset[r])
                print('\n')

        final_str = f' Total classified: {classified_percent}% ({classified_count})'
        print('+'+'-'*(len(final_str)-1)+'+')
        print(final_str)
        print('+'+'-'*(len(final_str)-1)+'+')
        print('\n')
        
if __name__ == "__main__":
        main()