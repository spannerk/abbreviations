from itertools import combinations, tee
import re
import pandas as pd
from pathlib import Path

class Abbreviator:
    def __init__(self, letter_val_filepath):
        with open(letter_val_filepath) as f:
            lines = f.readlines()
    
        self.letter_values = dict([l.strip().split() for l in lines])
    
    
    def standardise_phrase(self, phrase):
        new_phrase = re.sub("\'", "", phrase)
        new_phrase = re.sub("\W", " ", new_phrase)
        new_phrase = re.sub(" {2,}", " ", new_phrase)
        new_phrase = new_phrase.upper()
        return new_phrase
    
    
    def position_scores_per_letter(self, word):
        n = len(word)
        
        position_values = [0] + list(range(1, n-1))
        
        if n == 1:
            return position_values
        elif n==0:
            return []
        elif word[-1] == 'E':
            return position_values + [20]
        else:
            return position_values + [5]
        
    def letter_scores_per_letter(self, word):
        if len(word) > 1:
            return [0] + [int(self.letter_values[l]) for l in word[1:-1]] + [0]
        else:
            return [0]
    
    def scores_per_letter(self, word):
        return [sum(x) for x in zip(self.position_scores_per_letter(word), self.letter_scores_per_letter(word))]
    
    def phrase_scores_per_letter(self, phrase):
        for word in phrase.split():
            for score in self.scores_per_letter(word):
                yield score
                
    def squash_phrase(self, phrase):
        return re.sub(' ', '', phrase)
                
    def abbreviations_indicies(self, n):
        return combinations(range(0, n-1), 2)
    
    def generate_abbreviations_rows(self, original_phrase):
        standardised_phrase = self.standardise_phrase(original_phrase)
        squashed_phrase = self.squash_phrase(standardised_phrase)
        phrase_scores = list(self.phrase_scores_per_letter(standardised_phrase))
        
        phrase_length = len(squashed_phrase)
        for i, j in self.abbreviations_indicies(phrase_length):
            yield {'original_phrase': original_phrase
                   , 'abbreviation': "{}{}{}".format(squashed_phrase[0], squashed_phrase[i+1], squashed_phrase[j+1] )
                   , 'i_score': phrase_scores[i+1]
                   , 'j_score': phrase_scores[j+1] }
    
    def input_as_dict(self, input_phrases):
        for p in input_phrases:
            yield {'input_val': p}
    
    def input_to_df_rows(self, input_phrases):
        for p in input_phrases:
            for r in self.generate_abbreviations_rows(p):
                yield r

    def ingest_file(self, input_filepath):
        with open(input_filepath) as f:
            for line in f:
                yield line.strip()

    def process_dfs(self, originals_df, scores_df):

        # add together the second and third letter scores to get a score for the abbreviation
        scores_df['score'] = scores_df['i_score'] + scores_df['j_score']

        # only keep abbreviations that are only applied to a single phrase
        number_phrases_with_abb = scores_df.groupby('abbreviation')['original_phrase'].transform('nunique').copy()
        scores_df = scores_df[number_phrases_with_abb == 1]
        
        # filter to keep the best scores per phrase
        abbreviation_rank = scores_df.groupby('original_phrase')['score'].transform('rank', method='min').copy()
        scores_df = scores_df[abbreviation_rank==1]
        
        # in cases where two versions of the same abbreviation for a phrase both had the same score and so are both present, deduplicate
        scores_df.drop_duplicates(['original_phrase', 'abbreviation'], inplace=True)
        
        # where there are two equally good abbreviations, put into one row
        scores_df = scores_df.groupby('original_phrase')['abbreviation'].agg(lambda x: " ".join(x))

        # deduplicate the original phrases in case there were two the same in the input file
        originals_df.drop_duplicates(inplace=True)
        
        # merging the abbreviations back into the original list, to include the phrases that had no allowable combinations in the output, and make those blank
        abbreviations_df =  originals_df.merge(scores_df, how='left', left_on='input_val', right_index=True)
        abbreviations_df.fillna(" ", inplace=True)
        return abbreviations_df

    
    def run(self, input_filepath):
        
        input_data = self.ingest_file(input_filepath)

        input_1, input_2 = tee(input_data)

        scores_df = pd.DataFrame(self.input_to_df_rows(input_1))
        originals_df = pd.DataFrame(self.input_as_dict(input_2))

        results = self.process_dfs(originals_df, scores_df)
        
        output_filename = "gordon_{}_abbrevs.txt".format(Path(input_filepath).stem)
        results.stack().to_csv(output_filename, header=False, index=False)
        return "Abbreviations downloaded to {}".format(str(Path.cwd().joinpath(output_filename)))

