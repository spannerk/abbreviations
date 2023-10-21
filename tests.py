import unittest

class TestAbbreviator(unittest.TestCase):

    def setUp(self):
        from abbs import Abbreviator
        self.abbreviator = Abbreviator("data/values.txt")

    def test_standardise_phrase(self):
        self.assertEqual(self.abbreviator.standardise_phrase('C++ Code'), 'C CODE')
        self.assertEqual(self.abbreviator.standardise_phrase("More's Law"), 'MORES LAW')
        self.assertEqual(self.abbreviator.standardise_phrase("Object-oriented-programming"), 'OBJECT ORIENTED PROGRAMMING')
    
    def test_position_scores_per_letter(self):
        self.assertEqual(self.abbreviator.position_scores_per_letter('E'), [0])
        self.assertEqual(self.abbreviator.position_scores_per_letter('HORRIBLY'), [0, 1, 2, 3, 4, 5, 6, 5])
        self.assertEqual(self.abbreviator.position_scores_per_letter('HORRIBLE'), [0, 1, 2, 3, 4, 5, 6, 20])
        self.assertEqual(self.abbreviator.position_scores_per_letter(''), [])

if __name__ == '__main__':
    unittest.main()