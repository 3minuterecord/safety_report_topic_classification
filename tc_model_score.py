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
        sample_ref = 'model_hydraulic fluid or oil leak_fps'
        try:
                out_df = pd.read_csv(f"performance/{sample_ref}.csv", dtype=str)
                out_df.reset_index(inplace=True)    
                scores = [0]
                print(out_df)
                for r, doc in enumerate(out_df["text"]):
                        print('\n')
                        cat_title = f'{r+1} of {len(out_df)}'
                        print(cat_title)
                        print('='*len(cat_title))
                        print(doc)
                        print('\n')
                        trues, falses = scores.count(1), scores.count(2)
                        tots = trues+ falses
                        if tots == 0:
                                score_tally = f'T: {trues}\tF: {falses}'
                        else:
                                trues_per = round(100*trues/tots)
                                falses_per = round(100*falses/tots)
                                score_tally = f'T: {trues} ({trues_per}%), F: {falses} ({falses_per}%)'
                        print(score_tally)
                        # Exception handling for input that is not 1, 2 or 3
                        checkInputType = False
                        while not checkInputType :
                                score = input('Score (1: True, 2: False): ')
                                if score.isnumeric() and int(score) < 3 :
                                        checkInputType = True
                                        score = int(score)
                                        scores.append(score)
                out_df['scores'] = scores[1:]
                print('Writing scores...')
                out_df.to_csv(f'scored_samples/{sample_ref}_scored_predictions_{trues}-{falses}.csv', index=False)
                print('done \n')
        except:
                print('Error: Check if a valid file reference has been used...')      
if __name__ == "__main__":
        main()