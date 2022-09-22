import pandas as pd
import rule_book_functs as rbfuncts
from tqdm.notebook import tqdm

# Description:
# +--------------------------------------------------------------------+
# This script is used to manually evaluate each false positive (FP) 
# classification made by the a trained topic classification model.
# As the TC model is trained on rule book hits, not all classifications
# will be accurate and some true positives will have been missed.

# Main Steps:
# -----------
# 1. Load a csv of false postive classifications
# 2. Loop through and manually assess if false positive or true positive
#     - Did the rule book miss this narrative and TC model is correct? 
# 4. Save the corrected classification to output file
#     - Use the corrected file to adjust the TC model precision measure
# +--------------------------------------------------------------------+

def main():
        # Load test data
        sample_ref = 'model_hydraulic fluid or oil leak_fps'
        try:
                out_df = pd.read_csv(f"performance/{sample_ref}.csv", dtype=str)
                out_df.reset_index(inplace=True)    
                scores = [0]
                for r, doc in enumerate(out_df["text"]):
                        print('\n')
                        cat_title = f'{r+1} of {len(out_df)}'
                        print(cat_title)
                        print('='*len(cat_title))
                        print(doc)
                        print('\n')
                        trues, falses = scores.count(1), scores.count(2)
                        tots = trues + falses
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
                out_df.to_csv(f'scored_samples/{sample_ref}_scored_predictions_{trues_per}-{falses_per}_{trues}-{falses}.csv', index=False)
                print('done \n')
        except:
                print('Error: Check if a valid file reference has been used...')      
if __name__ == "__main__":
        main()