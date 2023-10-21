from itertools import combinations
import re
import pandas as pd

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
    
    def make_abbreviations_dataframe(self, input_filepath):
        originals = []
        
        scores_df = pd.DataFrame(data={'original_phrase': [], 'abbreviation':[], 'i_score':[], 'j_score':[]})
        with open(input_filepath) as f:
            for line in f:
                originals.append(line.strip())
                scores_df = pd.concat([scores_df, pd.DataFrame(self.generate_abbreviations_rows(line.strip()))])
        
        scores_df['score'] = scores_df['i_score'] + scores_df['j_score']
        
        scores_df['number_phrases_with_abb'] = scores_df.groupby('abbreviation')['original_phrase'].transform('nunique')
        
        scores_df = scores_df[scores_df['number_phrases_with_abb'] == 1]
        
        scores_df['abbreviation_rank'] = scores_df.groupby('original_phrase')['score'].transform('rank', method='min')
        scores_df = scores_df[scores_df['abbreviation_rank']==1]
        
        scores_df.drop_duplicates(['original_phrase', 'abbreviation'], inplace=True)
        
        scores_df = scores_df.groupby('original_phrase')['abbreviation'].agg(lambda x: " ".join(x))
        originals_df = pd.DataFrame(data={'input_val': originals})
        originals_df.drop_duplicates(inplace=True)
        
        return_df = originals_df.merge(scores_df, how='left', left_on='input_val', right_index=True)
        
        return_df.fillna(" ", inplace=True)
        
        return return_df