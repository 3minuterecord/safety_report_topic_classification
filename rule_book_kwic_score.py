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
        sample_ref = '220730103309'
        out_df = pd.read_csv(f"test_samples/{sample_ref}_100_sample_scores.csv", dtype=str)  
        classified_count = len(out_df)                
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
                # Exception handling for input that is not 1, 2 or 3
                checkInputType = False
                while not checkInputType :
                        score = input('Score (1: Good, 2: Fair, 3: Poor): ')
                        if score.isnumeric() and int(score) < 4 :
                                checkInputType = True
                                score = int(score)
                                scores.append(score)
        out_df['scores'] = scores[1:]
        print('Writing scores...')
        out_df.to_csv(f'scores/{sample_ref}_{classified_count}_scored_dataset.csv')
        print('done \n')
        print(scores)
              
if __name__ == "__main__":
        main()