# safety_report_tc
Safety report topic classification with transformer-based data augmentation

**TODO** - Check if data normalisation is required for fabricated data.

# Steps Implemented
The main steps of this project are as follows:
1. Combine source data & select free-text description of incidents (remove other columns).
    - Dataset is 3 columns (row ID, free-text description, and dataset ID).
2. Iterate through randomly selected samples of 100 incidents (rows) & build rules.
    - Rules added & adjusted during each iteration.
    - In parallel, build domain-specific synonym dictionary.
3. Stop iterating when coverage is above target (e.g., 70%).
    - Coverage is % of sample classified by the rule-book method.
4. Evaluate quality of rule book classifications (i.e., create scored samples).
    - Give classified narratives a score of 1, 2 or 3 by human/SME review.
    - 1: Good, 2: Fair and 3: Bad.
5. Confirm quality is acceptable (target greater than 70% good and less than 5% bad).
6. Loop through rule-by-rule and create subset dataset for each group/category.
7. Decide on focus (safety leading indicator) groups.
    - Each group is a minority group, i.e., rare/relatively scarce.
8. For each focus group, fine-tune a GPT2 decoder model.
9. For each focus group, create a set of tailored prompt rules.
    - Example prompt rule is 'operative noticed hydraulic leak'.
10. Use prompt rules and fine-tuned language model to create fake data (for augmentation).
    - Each prompt rule is used to create 'n' fake narratives.
11. Score uality of fake narratives using random sampling & manual review.
12. Use standard (baseline) text augmentation techniques to create modified data (for augmentation).
13. Train Bi-directional LSTM (BiLSTM) model as binary classifier for each group.
    - Begin with no treatment for class imbalance (no augmentation or under-sampling).
14. Train BiLSTM model using baseline data augmentation (BDA).
15. Train BiLSTM model using transformer-based data augmentation (TrDA).

# Folder Structure & Explanations

## 01_data
'source' contains raw input datasets (OSHA, ORGP & fabricated)
'ORGP' is the refence used for data provided by the private company (a multi-national energy services company providing engineering, construction, maintenance and operation services to the energy industry).
'fabricated' refers to data manually fabricated by SMEs (subject matter experts).

## 02_data_preparation
Scripts and notebooks used to prepare the source data for modelling.
- Data preparation (denoise, normalise, split) for topic classification
- Data preparation (creation) using baseline augmentation techniques

**Note**: Data preparation (creation) by language model is done in the language model sub-folder (07_language_models).

## 03_embeddings
Storage of embedding model data (e.g., GloVe and Elmo).
Elom is included for refernce and future work.

## 04_rule_book
Rule book rules (compiled directly in csv files by human/SME).
'_ ' used to separate rules.
'{}' used to denote 'synonym' or phrase permutation.
Separate 'rule' files are used for rule book classification and language model prompt generation.
Shared 'synonym.csv' file used. This file was created by human/SME review of domain/data.

Folder also contains various scripts for applying & processing rule book findings:
- rule_book_functs.py (helper functions for rule book implementation)
- rule_book_kwic.py (script for running rule book on source data)
- rule_book_kwic_coverage_chk.py (script to evaluate rule book coverage using random sampling)
- rule_book_kwic_create_test_sample.py (script for creating sample of 'n' classified narratives)
- rule_book_kwic_score.py (script for manually scoring the quality of rule book classifications)

**KWIC**: Reference to 'keyword in context' methodology. The basis of KWIC methodology is to search for a topic keyword (e.g., scaffold) and then process the pre, post and complete context (i.e., 'n' words before and after keyword find) using rules to determine if a 'hit' is found. A 'hit' is when a rule for a group is met and a classifciation is assigned. An incident description can have more than one 'hit', i.e., it can have multiple groups assigned.

## 05_coverage_checks
**Coverage**: Reference to what percentage of narratives are classified by the rule-book method. At the outset of the project the target coverage was 70%. The coverage checks are performed by running a collection (e.g., 30) of randomly selected samples (size 100). Running all rules on all data (over 93k incident narratives) takes a long time (several days) and a steady connection, hence the method of random sampling was effective without requiring several days of compute time.

## 06_scored samples
This folders contains the scored sample files. Samples were typically 100 incident narratives. The files contain the text narrative, the assigned classifications (i.e., categories) and the human/SME assigned score (1, 2 or 3). Scoring logic was as follows:

**Good**: All assigned classifications are accurate and no significant category is missing from the classification.
**Fair**: At least one significant category is assigned but some applicable categories could be missing or assigned incorrectly.
**Bad**: None of the assigned catehories are applicable to the accident description.

## 07_language_models
- GPT_fine_tuning_and_fake_generation.ipynb: Train (fine tune) GPT decorder model on group (subset) datasets created by rule book classification. This creates a language model that can create fake incident narratives in the context of a selected focus group (e.g., PPE non-compliance). The notebook also contains the block of code that creates the fake narratives from a list of input prompts.
- language_model_prompt_generation.py: Takes an input 'rule book' style csv file of prompt rules that incorporate synonyms and mutates to create a list of prompts that are used in the language model fake narrative generation step.
- language_model_score.py: Script used to score the quality of randomly selected fake narratives. An output file is created with the scored narratives.

## 08_output
This folder contains output from various analysis and postprocessing steps, e.g., :
- Trained models (datetime stamped in pickle format).
- Subset datasets created from rule book classification.

## 09_topic_classification
Notebooks for training topic classification models. The main model selected is a bi-directional LSTM model using GloVe embeddings. Various iterations of the model are presented:
- Base model with no treatment for class imbalance.
- Model with data augmentation by 'standard' text data augmentation techniques.
- Model with data augmentation by transformer based augmentation.

## 10_performance
Scripts for assessing performance of classification model output. As performance measures for the classification models are based on standard precision, recall and F1 measures that are calculated on the basis that rule book assigned classifications are 'true', there is a requirement to evaluate and adjust the measures. For example, the precision calculation is adjusted to reflect an adjusted false positive rate, i.e., a higher proportion of the false positives will actually be true positives. This is the case as the initial classifications are made by the rule-book and are not ground truth labels assigned by SMEs/domain experts. 

## 11_plots
Plots/figures generated with required formatting for insertion in the project (LaTex) report.

## 12_general_resources
General resources and tools used in certain steps, e.g., GB to US english dictionary.

## 13_test_samples
Storage area for rule book classified test samples.

## 14_reference_code
Some useful reference code for the project.

## 15_azure_funct_kwic
Work-in-progress code for deployment of the classifiers using Azure functions. Not part of the scope of the current project but something that is hoped will be added in a later stage.