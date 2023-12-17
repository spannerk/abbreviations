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

        # Apostrophes (') should be ignored completely
        new_phrase = re.sub("\'", "", phrase)

        # Any other sequences of non-letter characters are also ignored, 
        # but split the name into separate words.
        new_phrase = re.sub("\W", " ", new_phrase)
        new_phrase = re.sub(" {2,}", " ", new_phrase)

        # The abbreviations will consist entirely of upper case letters, so for the purpose of
        # finding the abbreviations all the letters can be regarded as upper case.
        new_phrase = new_phrase.upper()
        return new_phrase
    
    
    def position_scores_per_letter(self, word):
        n = len(word)

        # If a letter is the first letter of a word in the name then it has score 0.
        # If a letter is neither the first nor last letter of a word, then its score is the sum of
        # a position value, which is 1 for the second letter of a word, 2 for the third letter
        # and 3 for any other position
        position_values = [0] + [min(3, i) for i in range(1, n-1)]
        

        # e, if a letter is the last letter of a word in the name then it has score 5,
        # unless the letter is E, in which case the score is 20
        if n == 1:
            return position_values
        elif n==0:
            return []
        elif word[-1] == 'E':
            return position_values + [20]
        else:
            return position_values + [5]
        
    def letter_scores_per_letter(self, word):

        # If a letter is neither the first nor last letter of a word, then its score is the sum of
        # a position value, (...), plus a value based on how common/uncommon
        # this letter is in English: 1 for Q,Z, 3 for J,X, 6 for K, 7 for F,H,V,W,Y, 8 for
        # B,C,M,P, 9 for D,G, 15 for L,N,R,S,T, 20 for O,U, 25 for A,I and 35 for E. A
        # list of the values is in the file values.txt.

        if len(word) > 1:
            return [0] + [int(self.letter_values[l]) for l in word[1:-1]] + [0]
        elif len(word)==0:
            return []
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
        # Each abbreviation consists of the first letter of the name (you can assume that
        # the first character will always be a letter) followed by two further letters from the
        # name, in order.

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

        # The score for an abbreviation is the sum of scores for its second and third letters
        scores_df['score'] = scores_df['i_score'] + scores_df['j_score']

        # Any abbreviation which can be formed from more than one name on the list is excluded.
        # copy is used here to avoid trying to filter the dataframe based on transformations
        # of itself, see SettingWithCopy warning
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

