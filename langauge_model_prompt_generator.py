import pandas as pd
import rule_book_functs as rbfuncts
from datetime import datetime
import numpy as np

# Description:
# +--------------------------------------------------------------------+
# 1. To be added
# +--------------------------------------------------------------------+

def main():       
        # Load raw incident data
        rul_csv = pd.read_csv('rule_book/rule_book_prompts.csv')
        
        # Load the synonym database
        syns_data = pd.read_csv('rule_book/synonyms.csv')
        syns_data['syn'] = syns_data['syn'].apply(rbfuncts.replace_syns)

        tmp = [rbfuncts.expand_prompts(x, syns_data) for x in rul_csv["rules_all"]]
        
        groups = []
        outs = []
        for r in range(len(rul_csv)):
                group = rul_csv["group"].iloc[r]
                prompt = rul_csv["rules_all"].iloc[r]
                if isinstance(prompt, str):
                        groups.extend(rbfuncts.expand_prompts(group, syns_data))
                        outs.extend(rbfuncts.expand_prompts(prompt, syns_data))
                 
        outs = '_ '.join(outs)  
        outs = outs.split('_ ')             
        
        print('Writing list of language model prompts...')

        out_df = pd.DataFrame(groups, columns=['group'])
        out_df['prompts'] = str(outs)
        out_df.to_csv(f'rule_book/prompts.csv',  index=False)
        
if __name__ == "__main__":
        main()