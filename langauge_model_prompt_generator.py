import pandas as pd
import rule_book_functs as rbfuncts
from datetime import datetime
import re

# Description:
# +--------------------------------------------------------------------+
# This script mutates (expands) language model prompt rules that incorporate 
# synonyms. The mutated rules are joined into a single string separated
# using the '_ ' character. The single string can then be split when loaded
# & used as prompts for the language model to fabricate fake incident narratives.
# The language model is trained in a separate script. The language model prompt
# rules were generated using domain understanding. The use of rules incorporating
# synonyms allows a large number of prompts to be created from a small set of rules.

# This script only creates the expanded prompts, the use of the prompts to generate
# the fake narratives is covered in a separate script.

# Main Steps:
# -----------
# 1. Load rule book of language model prompts (user created rules)
# 2. Mutate the rules using the synonym dictionary (loaded from csv)
# 3. Write full list of prompts per rule group to prompts.csv
# +--------------------------------------------------------------------+

def main():       
        # Load raw incident data
        rul_csv = pd.read_csv('rule_book/language_prompts.csv')
        
        # Load the synonym database
        syns_data = pd.read_csv('rule_book/synonyms.csv')
        syns_data['syn'] = syns_data['syn'].apply(rbfuncts.replace_syns)
        
        groups = rul_csv.group
        outs = []
        counts = []
        for r in range(len(groups)):
                prompt = rul_csv["rules_all"].iloc[r]
                if isinstance(prompt, str):
                        mutate = rbfuncts.expand_prompts(prompt, syns_data)
                        mutate = "_ ".join(mutate)
                        mutate = re.sub(', ', '_ ', mutate)
                        mutate = re.sub(' +', ' ', mutate)
                        #outs.extend([f"['{mutate}']"])
                        outs.extend([f"{mutate}"])
                        count_ps = len(mutate.split('_ '))
                        counts.append(count_ps)
                else:
                        outs.extend(['']) 
                        counts.append(0)       
        
        print('Writing list of language model prompts...')

        # Write the mutated data as simple csv of DataFrame
        # The mutated prompt string will then be split when used in language model generation
        out_df = pd.DataFrame(groups, columns=['group'])
        out_df['counts'] = counts
        out_df['prompts'] = outs
        out_df.to_csv(f'rule_book/prompts.csv',  index=False)
        
        # Read in prompts and parse
        in_file = pd.read_csv('rule_book/prompts.csv')
        for i, gr in enumerate(in_file.group):
                # If present, get the raw prompt data
                if isinstance(gr, str):
                        in_prompt = in_file.prompts[i]
                        # Check for NaN, if not then parse to list
                        if not rbfuncts.isNaN(in_prompt):
                                in_prompt = str(in_prompt)
                                prompt_count = in_file.counts[i]
                                gr_str = f'\n{gr} ({prompt_count}):'
                                print(gr_str)
                                print('-'*(len(gr_str)-1))
                                prompts = in_prompt.split('_ ')
                                for p in prompts:
                                        print(p)
        
if __name__ == "__main__":
        main()