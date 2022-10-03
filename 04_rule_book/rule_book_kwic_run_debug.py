import pandas as pd
import rule_book_functs as rbfuncts
from tqdm.notebook import tqdm
from datetime import datetime
import sys

# Description:
# +--------------------------------------------------------------------+
# 1. ...
# +--------------------------------------------------------------------+

def main():
   
        rule_to_run = 'line strike'
        #chk_text = 'struck by falling object or equipment n e c an employee was breaking a truck seal when the dock door cable failed causing the door to fall and strike him on the back he suffered back and knee injuries'
        chk_text = ['excavator struck buried pipeline',
                    #'struck by swinging or slipping object, other than handheld, n.e.c. employees were trying to maneuver a metal pipe into place using a hoist when the swivel released and caused the pipe to suddenly lift up about 6 inches and strike the injured employee in the jaw.',
                    #'struck by swinging or slipping object, other than handheld',
                    'fall on same level due to tripping over an object  the employee was walking and stepped on a bin top cover which shifted, causing the employee to fall forward and strike his face on the tripper rail and a piece of conduit. the employee sustained a fractured eye socket/cheek bone.'
        ]
        docs = pd.DataFrame(chk_text, columns=['text'])
        
        # Load the synonym database
        syns_data = pd.read_csv('04_rule_book/synonyms.csv')
        syns_data['syn'] = syns_data['syn'].apply(rbfuncts.replace_syns)
        
        rul_csv = pd.read_csv('04_rule_book/rule_book_kwic.csv')
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

        unclassified_count = len(out_df.loc[(out_df.category == '*** Not Classified')])
        classified_count = len(out_df) - unclassified_count
        classified_count = "{:,}".format(classified_count)
        classified_percent = round(100 - round(100*(unclassified_count / len(out_df)), 1))

        print('\n')      
        for i in range(len(out_df)):
                print(f'"{out_df.text[i]}"\n')  
                print(f'>>> {out_df.category[i]} \n\n')
        final_str = f' Total classified: {classified_percent}% ({classified_count})'
        print('+'+'-'*(len(final_str)-1)+'+')
        print(final_str)
        print('+'+'-'*(len(final_str)-1)+'+')
        print('\n')
        
if __name__ == "__main__":
        main()