from unittest.mock import MagicMock
import unittest

from indexer import State, query, index, remove, Package, ERROR, OK, FAIL

class TestQuery(unittest.TestCase):
    def test_no_such_pkg(self):
        state = State({'vim': Package('vim', [])}, MagicMock())
        result = query(state, 'vi')
        self.assertEqual(result, FAIL)

    def test_pkg_found(self):
        state = State({'vim': Package('vim', [])}, MagicMock())
        result = query(state, 'vim')
        self.assertEqual(result, OK)

class TestIndex(unittest.TestCase):
    def test_new_pkg_with_seen_deps(self):
        store = {
            'coffee': Package('coffee', []),
            'tea': Package('tea', []),
        }
        state = State(store, MagicMock())
        result = index(state, 'vim', ['coffee', 'tea'])
        self.assertEqual(result, OK)
        pkg = store['vim']
        self.assertEqual(pkg.name, 'vim')
        self.assertEqual(set(pkg.dependencies), set(['coffee', 'tea']))
        self.assertEqual(store['coffee'].children, ['vim'])
        self.assertEqual(store['tea'].children, ['vim'])

    def test_new_pkg_without_seen_deps(self):
        store = {
            'yerba': Package('yerba', []),
        }
        state = State(store, MagicMock())
        result = index(state, 'vim', ['coffee', 'tea'])
        self.assertEqual(result, FAIL)
        self.assertEqual(list(store.keys()), ['yerba'])

    def test_new_pkg_without_deps(self):
        store = {
            'yerba': Package('yerba', []),
        }
        state = State(store, MagicMock())
        result = index(state, 'vi', [])
        self.assertEqual(result, OK)
        self.assertEqual(store['vi'].name, 'vi')
        self.assertEqual(store['vi'].dependencies, [])

    def test_seen_pkg(self):
        store = {
            'yerba': Package('yerba', []),
        }
        state = State(store, MagicMock())
        result = index(state, 'yerba', [])
        self.assertEqual(result, OK)

class TestRemove(unittest.TestCase):
    def test_unknown_pkg(self):
        store = {
            'coffee': Package('coffee', []),
        }
        state = State(store, MagicMock())
        result = remove(state, 'tea')
        self.assertEqual(result, OK)
        self.assertEqual(list(store.keys()), ['coffee'])

    def test_known_pkg_with_children(self):
        store = {
            'coffee': Package('coffee', []),
            'tea': Package('tea', []),
        }
        state = State(store, MagicMock())
        result = index(state, 'vim', ['coffee', 'tea'])
        self.assertEqual(result, OK)
        result = remove(state, 'coffee')
        self.assertEqual(result, FAIL)
        self.assertEqual(set(store.keys()), set(['coffee', 'tea', 'vim']))

    def test_known_pkg(self):
        store = {
            'coffee': Package('coffee', []),
            'tea': Package('tea', []),
        }
        state = State(store, MagicMock())
        result = index(state, 'vim', ['coffee', 'tea'])
        self.assertEqual(result, OK)
        result = remove(state, 'vim')
        self.assertEqual(result, OK)
        self.assertEqual(set(store.keys()), set(['coffee', 'tea',]))
