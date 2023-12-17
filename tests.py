import unittest
import pandas as pd
import re

class TestAbbreviator(unittest.TestCase):

    def setUp(self):
        from abbs import Abbreviator
        self.abbreviator = Abbreviator("data/values.txt")

    def test_standardise_phrase(self):
        # Examples: 
        # (i) “Object-oriented programming” has three words “OBJECT”, “ORIENTED”, and
        # “PROGRAMMING”, 
        # (ii) “Moore’s Law” has two words “MOORES” and “LAW”.

        self.assertEqual(self.abbreviator.standardise_phrase('C++ Code'), 'C CODE')
        self.assertEqual(self.abbreviator.standardise_phrase("More's Law"), 'MORES LAW')
        self.assertEqual(self.abbreviator.standardise_phrase("Object-oriented programming"), 'OBJECT ORIENTED PROGRAMMING')
    
    def test_letter_order(self):
        # for example, for “Data Engineering”,
        # “DTA” and “DEG” are acceptable abbreviations (there are many others),
        # while “DEA” and “ATA” are not

        test_abbs = [i['abbreviation'] for i in self.abbreviator.generate_abbreviations_rows('Data Engineering')]
        self.assertIn('DTA', test_abbs)
        self.assertIn('DEG', test_abbs)
        self.assertNotIn('DEA', test_abbs)
        self.assertNotIn('ATA', test_abbs)

    def test_position_scores_per_letter(self):

        self.assertEqual(self.abbreviator.position_scores_per_letter('E'), [0])
        self.assertEqual(self.abbreviator.position_scores_per_letter('HORRIBLY'), [0, 1, 2, 3, 3, 3, 3, 5])
        self.assertEqual(self.abbreviator.position_scores_per_letter('HORRIBLE'), [0, 1, 2, 3, 3, 3, 3, 20])
        self.assertEqual(self.abbreviator.position_scores_per_letter(''), [])
        self.assertEqual(self.abbreviator.position_scores_per_letter('HE'), [0,20])

    def test_letter_scores_per_letter(self):
        self.assertEqual(self.abbreviator.letter_scores_per_letter('E'), [0])
        self.assertEqual(self.abbreviator.letter_scores_per_letter('HORRIBLY'), [0, 20, 15, 15, 25, 8, 15, 0])
        self.assertEqual(self.abbreviator.letter_scores_per_letter('HORRIBLE'), [0, 20, 15, 15, 25, 8, 15, 0])
        self.assertEqual(self.abbreviator.letter_scores_per_letter(''), [])
        self.assertEqual(self.abbreviator.letter_scores_per_letter('HE'), [0,0])

    def test_oop_scores(self):
        # Thus in the case of “Object-oriented programming”, the abbreviation OOP (OBJECT
        # ORIENTED PROGRAMMING) will have score 0 because each letter is the start of
        # its word, while the abbreviation OAN (OBJECT ORIENTED PROGRAMMING)
        # has score 46 (0 for O, 3 for the position of A, 3 for the position of N, plus 25 for the
        # value of A and 15 for the value of N).

        test_abbs = {r['abbreviation']: r['i_score'] +  r['j_score'] for r in self.abbreviator.generate_abbreviations_rows('Object-oriented programming')}
        self.assertEqual(test_abbs['OOP'], 0)
        self.assertEqual(test_abbs['OAN'], 46)

    def test_all_abbrevs_example(self):
        fname = "data\example.txt"
        example_input_data = list(self.abbreviator.ingest_file(fname))
        self.assertListEqual(example_input_data, ['Cold', 'Cool', 'C++ Code'])

        example_scores_df = pd.DataFrame(self.abbreviator.input_to_df_rows(example_input_data))
        example_scores_df['score'] = example_scores_df['i_score'] + example_scores_df['j_score']
        example_scores_df = example_scores_df[['original_phrase', 'abbreviation', 'score']]
        # note this expected df contains one more line than in the assignment example
        # because the deduplication step happens afterwards
        expected_df = pd.read_csv("data\example_abbreviations.csv")

        pd.testing.assert_frame_equal(
            expected_df.sort_values(['original_phrase', 'abbreviation', 'score'])
            , example_scores_df.sort_values(['original_phrase', 'abbreviation', 'score']))
        
    def test_example_result(self):
        example_outfile = self.abbreviator.run("data\example.txt")
        self.assertRegexpMatches(example_outfile, ".*gordon_example_abbrevs\.txt")
        produced_fname = re.sub("Abbreviations downloaded to ", "", example_outfile)
        with open(produced_fname) as f:
            self.assertListEqual([s.strip() for s in f.readlines()], ["Cold", "CLD", "Cool", "COO", "C++ Code", "CCD"])

if __name__ == '__main__':
    unittest.main()