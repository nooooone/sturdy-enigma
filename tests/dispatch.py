import unittest
from unittest.mock import Mock, patch

from indexer import dispatch, ERROR, OK, CommandParsingError

class TestDispatch(unittest.TestCase):
    def test_ok_commands(self):
        with patch('indexer.query', return_value=OK) as m:
            result = dispatch(Mock(), b'QUERY|vim|\n')
            self.assertEqual(result, OK)
            self.assertTrue(m.called)

        with patch('indexer.remove', return_value=OK) as m:
            result = dispatch(Mock(), b'REMOVE|emacs|\n')
            self.assertEqual(result, OK)
            self.assertTrue(m.called)

        with patch('indexer.index', return_value=OK) as m:
            result = dispatch(Mock(), b'INDEX|nano|\n')
            self.assertEqual(result, OK)
            self.assertTrue(m.called)

        with patch('indexer.index', return_value=OK) as m:
            result = dispatch(Mock(), b'INDEX|nano|coffee,tea,yerba\n')
            self.assertEqual(result, OK)
            self.assertTrue(m.called)

    def test_malformed_command(self):
        with patch('indexer.parse_command', side_effect=CommandParsingError()):
            result = dispatch(Mock(), b'garbage')
            self.assertEqual(result, ERROR)


