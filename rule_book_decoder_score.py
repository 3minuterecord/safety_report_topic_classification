import pandas as pd
import rule_book_functs as rbfuncts
from tqdm.notebook import tqdm

# Description:
# +--------------------------------------------------------------------+
# 1. Load a csv of fabricated incident descriptions by file reference
# 2. Randomly sample 100 descriptions from the dataset
# 3. Loop through and manually score each fabricated incident
#     - Does it make sense? 
#     - Is it close to a human-written report? 
# 4. Save scores to output file
# +--------------------------------------------------------------------+

def main():
        # Load test data
        sample_ref = 'hydraulic fluid or oil leak_7920'
        sample_size = 100
        try:
                out_df = pd.read_csv(f"data/fabricated/{sample_ref}.csv", dtype=str)
                out_df = out_df.sample(sample_size) 
                out_df.reset_index(inplace=True)    
                scores = [0]
                for r, doc in enumerate(out_df["text"]):
                        print('\n')
                        cat_title = f'{r+1}: {out_df.group[r]}'
                        print(cat_title)
                        print('='*len(cat_title))
                        print(doc)
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
                out_df.to_csv(f'scored_samples/{sample_ref}_scored_dataset_{goods_per}-{fairs_per}-{badas_per}.csv', index=False)
                print('done \n')
        except:
                print('Error: Check if a valid file reference has been used...')      
if __name__ == "__main__":
        main()