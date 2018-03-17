import unittest
from godirec.core import Tags

class TagsTests(unittest.TestCase):

    def setUp(self):
        self.tags = Tags()
        self.expected_dict = {
                'album': '',
                'artist': '',
                'comment': 'Comment',
                'date': '',
                'genre': '',
                'title': 'Title Set',
                'tracknumber': ''
                }
        self.expected_tag_names = list(self.expected_dict.keys())
        self.expected_tag_names.sort()

    def test_initialization(self):
        for tag_name in self.expected_dict.keys():
            self.assertEqual(self.tags[tag_name], '')

    def test_set_tag_via_dict(self):
        self.tags['title'] = "set title"
        self.assertEqual(self.tags.title, 'set title');

    def test_get_all_tag_names(self):
        tag_names = self.tags.keys()
        tag_names.sort()
        self.assertListEqual(tag_names, self.expected_tag_names)

    def test_get_tags_as_dict(self):
        self.tags['title'] = 'Title Set'
        self.tags['comment'] = 'Comment'
        tags_dict = self.tags.dump()
        self.assertDictEqual(tags_dict, self.expected_dict)
