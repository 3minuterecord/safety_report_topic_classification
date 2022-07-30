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
        # Load test data
        out_df = pd.read_csv("test_samples/220730103309_100_sample_scores.csv", dtype=str)  
                        
        scores = [0]
        for r, doc in enumerate(out_df["text"]):
                print('\n')
                cat_title = f'{r+1}: {out_df.category[r]}'
                print(cat_title)
                print('='*len(cat_title))
                print(doc)
                print('~ ' + out_df.dset[r])
                print('\n')
                goods, fairs, bads = scores.count(1), scores.count(2), scores.count(3)
                tots = goods + fairs + bads
                if tots == 0:
                        score_tally = f'G: {goods}, F: {fairs}, B: {bads}'
                else:
                        score_tally = f'G: {goods} ({round(100*goods/tots)}%), F: {fairs} ({round(100*fairs/tots)}%), B: {bads} ({round(100*bads/tots)}%)'
                print(score_tally)
                # TODO - Add exception handling to this input
                score = input('Score (1: Good, 2: Fair, 3: Poor): ')
                score = int(score)
                scores.append(score)
        out_df['scores'] = scores
        
        print('Writing scores...')
        print('done \n')
        
        print(scores)
       
        
if __name__ == "__main__":
        main()