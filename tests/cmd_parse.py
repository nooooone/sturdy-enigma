import unittest

from indexer import parse_command, CommandParsingError

class TestCommandParsing(unittest.TestCase):
    def test_invalid_commands(self):
        invalid_commands = ['INDE', 'BLA', 'REM', 'remove', 'query', 'index',
                            'XEDNI', 'INDEX\n', 'IN DEX',]
        for invalid_cmd in invalid_commands:
            with self.assertRaises(CommandParsingError, msg=invalid_cmd):
                bs = '{}|vim|abc,def\n'.format(invalid_cmd).encode('utf-8')
                parse_command(bs)

    def test_malformed_commands(self):
        invalid_lines = ['INDEX|vi vim improved|tea,coffee\n',
                         'REMOVE|gn:arly|\n',
                         'INDEX|vim|coffee',
                         'INDEX|vim,blarf|coffee\n',
                         'INDEX\n|vim\n|coffee\n',]
        for invalid_line in invalid_lines:
            with self.assertRaises(CommandParsingError, msg=invalid_line):
                parse_command(invalid_line.encode('utf-8'))

    def test_ok_commands(self):
        pairs = [('INDEX|vim|coffee,tea,bread\n', 
                  ('INDEX', 'vim', ['coffee', 'tea', 'bread'])),
                 ('REMOVE|vim|\n',
                  ('REMOVE', 'vim', [])),
                 ('REMOVE|vim|foo,bar,baz\n',
                  ('REMOVE', 'vim', [])),
                 ('QUERY|vim|\n',
                  ('QUERY', 'vim', [])),
                 ('QUERY|vim|foo,bar\n',
                  ('QUERY', 'vim', [])),
                 ('INDEX|vim|\n',
                  ('INDEX', 'vim', [])),
                 ('INDEX|vim|foo,bar,baz,\n',
                  ('INDEX', 'vim', ['foo', 'bar', 'baz'])),
                 # TODO the directions don't say to support unicode, so we don't:
                 #('INDEX|\U0001F4A9|yes,no,maybe\n',
                 # ('INDEX', '\U0001F4A9', ['yes', 'no', 'maybe'])),
        ]
        for line, output in pairs:
            self.assertEqual(parse_command(line.encode('utf-8')),
                             output,
                             msg=line)

if __name__ == '__main__':
    unittest.main()


