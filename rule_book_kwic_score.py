from cgitb import reset
import pandas as pd
import rule_book_functs as rbfuncts
from tqdm.notebook import tqdm
import time

# Description:
# +--------------------------------------------------------------------+
# 1. Load a test sample using its datetime reference
# 2. Loop through and manually score each classification
# 3. Save scores to output file
# +--------------------------------------------------------------------+

def main():
        # Load test data
        sample_ref = '220806193242'
        try:
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
                                score_tally = f'G: {goods}\tF: {fairs}\tB: {bads}'
                        else:
                                goods_per = round(100*goods/tots)
                                fairs_per = round(100*fairs/tots)
                                badas_per = round(100*bads/tots)
                                score_tally = f'G: {goods} ({goods_per}%), F: {fairs} ({fairs_per}%), B: {bads} ({badas_per}%)'
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
                out_df.to_csv(f'scores/{sample_ref}_{classified_count}_scored_dataset_{goods_per}-{fairs_per}-{badas_per}.csv', index=False)
                print('done \n')
        except:
                print('Error: Check if a valid file reference has been used...')      
if __name__ == "__main__":
        main()