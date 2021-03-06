#  Copyright 2008 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from copy import deepcopy
from os.path import dirname, join, normcase

import unittest

from mabot.model.io import IO
from mabot.model import model
from mabot.model.model import ManualMessage


class _TestAddingData(unittest.TestCase):

    def setUp(self):
        data = normcase(join(dirname(__file__), 'data', 'root_suite'))
        self.suite = IO().load_data(data)
        self.other_suite = deepcopy(self.suite)
        self.test = self.suite.suites[1].tests[0]
        self.other_test = self.other_suite.suites[1].tests[0]

    def tearDown(self):
        model.DATA_MODIFIED.status = False


class TestAddDataFromOtherItem(_TestAddingData):

    def test_adding_suites_sub_suites(self):
        self.other_suite.suites[1].tests[0].set_all('PASS')
        self.suite.add_results(self.other_suite)
        self.assertEquals(self.suite.suites[1].tests[0].status, 'PASS')

    def test_adding_suites_sub_suites_with_old_naming(self):
        self.other_suite.name = 'Root SUITE'
        self.other_suite.suites[1].tests[0].name = 'tc_with_keywords'
        self.other_suite.suites[1].tests[0].keywords[0].name = 'uk_1'
        self.other_suite.suites[1].tests[0].set_all('PASS')
        self.suite.add_results(self.other_suite)
        self.assertEquals(self.suite.suites[1].tests[0].status, 'PASS', 
                          'test results are not added')
        self.assertEquals(self.suite.suites[1].tests[0].keywords[0].status,
                          'PASS', 'keyword results are not added')

    def test_adding_suites_tests(self):
        self.other_suite.suites[1].tests[0].set_all('PASS')
        self.suite.add_results(self.other_suite)
        self.assertEquals(self.suite.suites[0].tests[0].status, 'FAIL')
        self.assertEquals(self.suite.suites[1].tests[0].status, 'PASS')

    def test_adding_suites_tests_with_new_test_with_not_adding_missing(self):
        test = deepcopy(self.other_suite.suites[0].tests[0])
        test.name = 'Added Test'
        self.other_suite.suites[0].tests.append(test)
        self.suite.add_results(self.other_suite, False, None)
        self.assertEquals(len(self.suite.suites[0].tests), 1)
        self.assertNotEquals(self.suite.suites[0].tests[0].name, 'Added Test')
        self.assertEquals(model.DATA_MODIFIED.is_modified(), True)

    def test_adding_suites_tests_with_new_test_to_end_with_adding_missing(self):
        test = deepcopy(self.other_suite.suites[0].tests[0])
        test.name = 'Added Test'
        self.other_suite.suites[0].tests.append(test)
        self.suite.add_results(self.other_suite, True, True)
        self.assertEquals(len(self.suite.suites[0].tests), 2)
        self.assertEquals(self.suite.suites[0].tests[1].name, 'Added Test')
        self.assertEquals(model.DATA_MODIFIED.is_modified(), False)

    def test_adding_suites_tests_with_new_test_to_beginning_with_adding_missing(self):
        test = deepcopy(self.other_suite.suites[0].tests[0])
        test.name = 'Added Test'
        self.other_suite.suites[0].tests.insert(0, test)
        self.suite.add_results(self.other_suite, add_from_xml=True)
        self.assertEquals(len(self.suite.suites[0].tests), 2)
        self.assertEquals(self.suite.suites[0].tests[1].name, 'Added Test',
                          "Should be added at the end, because there is no order.")
        self.assertEquals(model.DATA_MODIFIED.is_modified(), False)

    def test_adding_suites_tests_with_removed_test_in_beginning(self):
        self._test_removed_test(0, False)

    def test_adding_suites_tests_with_removed_test_in_beginning_with_adding_missing(self):
        self._test_removed_test(0, True)

    def test_adding_suites_tests_with_removed_test_in_middle(self):
        self._test_removed_test(1, False)

    def test_adding_suites_tests_with_removed_test_in_middle_with_adding_missing(self):
        self._test_removed_test(1, True)

    def test_adding_suites_tests_with_removed_test_in_end(self):
        self._test_removed_test(2, False)

    def test_adding_suites_tests_with_removed_test_in_end_with_adding_missing(self):
        self._test_removed_test(2, True)

    def _test_removed_test(self, index, add_from_xml):
        self.other_suite.suites[2].set_all('PASS')
        self.other_suite.suites[2].tests.pop(index)
        self.suite.add_results(self.other_suite)
        self.assertEquals(len(self.suite.suites[2].tests), 3)
        self.assertEquals(self.suite.suites[2].tests[0].status,
                          index == 0 and 'FAIL' or 'PASS')
        self.assertEquals(self.suite.suites[2].tests[1].status,
                          index == 1 and 'FAIL' or 'PASS')
        self.assertEquals(self.suite.suites[2].tests[2].status,
                          index == 2 and 'FAIL' or 'PASS')

    def test_adding_suites_sub_suites_with_new_sub_suite(self):
        suite = deepcopy(self.other_suite.suites[0])
        suite.name = 'Added Suite'
        self.other_suite.suites.append(suite)
        self.suite.add_results(self.other_suite, add_from_xml=False)
        self.assertEquals(len(self.suite.suites), 3)
        self.assertFalse('Added Test' in [s.name for s in self.suite.suites],
                         "When add_from_xml is false, suite should not be added!")

    def test_adding_suites_sub_suites_with_new_sub_suite_with_adding_missing(self):
        suite = deepcopy(self.other_suite.suites[0])
        suite.name = 'Added Suite'
        self.other_suite.suites.append(suite)
        self.suite.add_results(self.other_suite, add_from_xml=True)
        self.assertEquals(len(self.suite.suites), 4)
        self.assertEquals('Added Suite', self.suite.suites[3].name)

    def test_adding_suites_sub_suites_with_removed_sub_suite(self):
        self._test_removed_suite(False)

    def test_adding_suites_sub_suites_with_removed_sub_suite_with_adding_missing(self):
        self._test_removed_suite(True)

    def _test_removed_suite(self, add_from_xml):
        self.other_suite.suites.pop(1)
        self.other_suite.set_all('PASS')
        self.suite.add_results(self.other_suite, add_from_xml=add_from_xml)
        self.assertEquals(self.suite.suites[0].tests[0].status, 'PASS')
        self.assertEquals(self.suite.suites[1].tests[0].status, 'FAIL')
        self.assertEquals(self.suite.suites[2].tests[0].status, 'PASS')

    def test_adding_tests_status_and_message(self):
        test = self.other_suite.suites[2].tests[1]
        test.message = 'New Message'
        test.status = 'PASS'
        self.suite.add_results(self.other_suite)
        self.assertEquals(self.suite.suites[2].tests[1].status, test.status)
        self.assertEquals(self.suite.suites[2].tests[1].message, test.message)

    def test_adding_tests_times(self):
        test = self.other_suite.suites[2].tests[1]
        test.starttime = '20080121 21:01:08'
        test.endtime = '20080121 21:01:20'
        self.suite.add_results(self.other_suite)
        self.assertEquals(self.suite.suites[2].tests[1].starttime, test.starttime)
        self.assertEquals(self.suite.suites[2].tests[1].endtime, test.endtime)

    def test_adding_test_results_when_tags_added(self):
        test = self.suite.suites[0].tests[0]
        other_test = deepcopy(test)
        other_test.tags.append('new-tag')
        test.add_results(other_test, False, None)
        self.assertEquals(test.tags, ['new-tag', 'tag-1', 'tag-2', 'tag-3'])
        self.assertFalse(test.is_modified)

    def test_adding_test_results_when_tags_removed(self):
        test = self.suite.suites[0].tests[0]
        other_test = deepcopy(test)
        other_test.tags.pop(1)
        test.add_results(other_test, False, None)
        self.assertEquals(test.tags, ['tag-1', 'tag-2', 'tag-3'])
        self.assertTrue(test.is_modified)

    def test_adding_test_results_when_tags_added_and_removed(self):
        test = self.suite.suites[0].tests[0]
        other_test = deepcopy(test)
        other_test.tags.pop(1)
        other_test.tags.append('new-tag')
        test.add_results(other_test, False, None)
        self.assertEquals(test.tags, ['new-tag', 'tag-1', 'tag-2', 'tag-3'])
        self.assertTrue(test.is_modified)

    def test_adding_tests_keywords(self):
        self.other_suite.suites[1].tests[0].set_all('PASS')
        self.suite.add_results(self.other_suite)
        self.assertEquals(self.suite.suites[1].tests[0].keywords[0].status, 'PASS')
        self.assertEquals(self.suite.suites[1].tests[0].keywords[0].keywords[0].status, 'PASS')

    def test_adding_tests_keywords_reading_from_xml(self):
        self.other_suite.suites[1].tests[0].set_all('PASS')
        self.other_suite.save()
        self.assertEquals(self.other_suite.suites[1].tests[0].keywords[0].status, 'PASS')
        self.suite.add_results(self.other_suite, True, True)
        self.assertEquals(self.suite.suites[1].tests[0].keywords[0].status, 'PASS')
        self.assertEquals(self.suite.suites[1].tests[0].keywords[0].keywords[0].status, 'PASS')

    def test_adding_test_results_with_added_keyword_not_from_xml(self):
        test = self.suite.suites[1].tests[0]
        kw = deepcopy(test.keywords[0])
        other_test = deepcopy(test)
        other_test.keywords.append(kw)
        self._add_info(other_test)
        test.add_results(other_test, False, None)
        self._tests_are_unequal(test, other_test)
        self.assertEquals(model.DATA_MODIFIED.is_modified(), True)

    def test_adding_test_results_with_added_keyword_from_xml(self):
        test = self.suite.suites[1].tests[0]
        kw = deepcopy(test.keywords[0])
        other_test = deepcopy(test)
        other_test.keywords.append(kw)
        self._add_info(other_test)
        test.add_results(other_test, True, True)
        self._tests_are_unequal(test, other_test)
        self.assertEquals(model.DATA_MODIFIED.is_modified(), False)

    def _add_info(self, test):
        test.status = 'PASS'
        test.message = 'Hello'
        test.starttime = '20010101 21:21:21.000'
        test.endtime = '20010101 21:21:21.000'
        test.tags =  ['missing-tag']

    def _tests_are_unequal(self, test, other_test):
        self.assertNotEquals(test.status, other_test.status)
        self.assertNotEquals(test.message, other_test.message)
        self.assertNotEquals(test.starttime, other_test.starttime)
        self.assertNotEquals(test.endtime, other_test.endtime)
        self.assertNotEquals(test.tags, other_test.tags)

    def test_adding_test_results_with_removed_keyword(self):
        test = self.suite.suites[1].tests[0]
        other_test = deepcopy(test)
        other_test.keywords.pop(1)
        other_test.status = 'PASS'
        test.add_results(other_test, False, None)
        self.assertEquals(test.status, 'FAIL')

    def test_adding_tests_keywords_with_added_keyword(self):
        kw = deepcopy(self.other_suite.suites[1].tests[0].keywords[0].keywords[0])
        kw.name = 'Added KW'
        self.other_suite.suites[1].tests[0].keywords[0].keywords.append(kw)
        self.other_suite.set_all('PASS')
        self.suite.add_results(self.other_suite)
        self.assertEquals(len(self.suite.suites[1].tests[0].keywords[0].keywords), 1)
        result_kw = self.suite.suites[1].tests[0].keywords[0].keywords[0]
        self.assertNotEquals(result_kw.name, 'Added KW')
        self.assertEquals(result_kw.status, 'FAIL')

    def test_adding_tests_keywords_with_renamed_keyword(self):
        self.other_suite.suites[1].tests[0].keywords.pop(2)
        self.other_suite.set_all('PASS')
        self.suite.add_results(self.other_suite)
        self.assertEquals(len(self.suite.suites[1].tests[0].keywords), 5)
        for kw in self.suite.suites[1].tests[0].keywords:
            self.assertEquals(kw.status, 'FAIL')

    def test_adding_tests_keywords_with_removed_keyword(self):
        self.other_suite.suites[1].tests[0].keywords[0].keywords[0].name = 'Changed'
        self.other_suite.set_all('PASS')
        self.suite.add_results(self.other_suite)
        self.assertEquals(len(self.suite.suites[1].tests[0].keywords), 5)
        for kw in self.suite.suites[1].tests[0].keywords:
            self.assertEquals(kw.status, 'FAIL')


class TestSavingWhenChangesInKeywords(_TestAddingData):

    def setUp(self):
        self._orig_dialog = model.tkMessageBox
        self.dialog = MockDialog()
        model.tkMessageBox = self.dialog.call
        _TestAddingData.setUp(self)
        self.other_test.keywords.pop(1)
        self.other_test.endtime = '20080101 10:10:10.000'
        self.test.status = 'PASS'
        self.test.message = 'Hello'

    def tearDown(self):
        model.tkMessageBox = self._orig_dialog

    def test_changes_in_kws_and_saving_data_when_own_kws_uptodate_and_others_old(self):
        self.test.add_results(self.other_test, True, self.dialog.call)
        self.assertEquals(self.test.status, 'PASS')
        self.assertEquals(self.test.message, 'Hello')
        self.assertEquals(self.test.keywords[0].name, 'UK1')
        self.assertEquals(len(self.dialog.messages), 0)
        self.assertFalse(self.test.is_modified)

    def test_changes_in_kws_and_saving_data_when_own_kws_old_and_others_uptodate(self):
        self.test.tags.append('extra')
        self.other_test.add_results(self.test, True, self.dialog.call)
        self.assertEquals(self.other_test.status, 'PASS')
        self.assertEquals(self.other_test.message, 'Hello')
        self.assertEquals(self.other_test.keywords[0].name, 'UK1')
        self.assertEquals(len(self.dialog.messages), 0)
        self.assertTrue('extra' in self.other_test.tags)
        self.assertTrue(self.other_test.is_modified)

    def test_changes_in_kws_and_saving_data_when_own_kws_old_and_others_old(self):
        self.test.keywords.pop(2)
        self.test.add_results(self.other_test, True, self.dialog.call)
        self.assertEquals(self.test.status, 'FAIL')
        self.assertEquals(self.test.message, 'Not Executed!')
        self.assertEquals(self.test.keywords[0].name, 'UK1')
        self.assertEquals(self.test.keywords[1].name, 'Keyword1')
        self.assertEquals(self.test.keywords[2].name, 'Keyword2')
        self.assertEquals(self.test.keywords[3].name, 'UK2')
        expected = """Keywords of test 'Root Suite.Sub Suite2.TC With Keywords' were updated from the data source.
Therefore changes made to those keywords could not be saved.
"""
        self.assertEquals(self.dialog.messages[0][1], expected)
        self.assertTrue(self.test.is_modified)

class TestHasSameKeywords(_TestAddingData):

    def test_has_same_keywords_same_count_same_names_same_children(self):
        self.assertTrue(self.test._has_same_keywords(self.other_test))

    def test_has_same_keywords_different_count(self):
        self.other_test.keywords.pop(1)
        self.assertFalse(self.test._has_same_keywords(self.other_test))

    def test_has_same_keywords_same_count_different_names(self):
        self.test.keywords[3].name = 'different name'
        self.assertFalse(self.test._has_same_keywords(self.other_test))

    def test_has_same_keywords_same_count_same_names_different_children(self):
        self.test.keywords[3].keywords.pop(0)
        self.assertFalse(self.test._has_same_keywords(self.other_test))

class TestLoadOther(_TestAddingData):

    def setUp(self):
        _TestAddingData.setUp(self)
        self.mock = MockDialog()

    def test_load_other_when_starting_eq_no_override_method(self):
        self.assertTrue(self.test._load_other(self.other_test, None))

    def test_load_other_when_no_modifications(self):
        self.assertFalse(self.test._load_other(self.other_test, True))

    def test_load_other_when_other_has_modifications(self):
        self.test.is_modified = False
        self.other_test.endtime = '20080101 10:10:10.100'
        self.assertTrue(self.test._load_other(self.other_test, True))

    def _modify_both_items(self):
        self.test.is_modified = True
        self.other_test.status = 'PASS'
        self.other_test.message = 'working'
        self.other_test.tags = ['tag-1', 'tag-2']
        self.other_test.endtime = '20080101 10:10:10.100'

    def test_load_other_when_both_have_modifications(self):
        self._modify_both_items()
        self.mock.return_ = True
        self.assertTrue(self.test._load_other(self.other_test, self.mock.call))
        self.mock.return_ = False
        self.assertFalse(self.test._load_other(self.other_test, self.mock.call))
        expected = """Test 'Root Suite.Sub Suite2.TC With Keywords' updated by someone else!
Your test information:
Status: FAIL
Message: Not Executed!
Tags: 

Other test information:
Status: PASS
Message: working
Tags: tag-1, tag-2

Do you want your changes to be overridden?"""
        self.assertEqual(self.mock.messages[0],
                         ("Conflicting Test Results!", expected))

    def test_load_other_when_both_have_modifications_status_is_different(self):
        self._modify_both_items()
        self.test.message = self.other_test.message
        self.mock.return_ = True
        self.assertTrue(self.test._load_other(self.other_test, self.mock.call))
        self.assertFalse(self.test.message in self.mock.messages[0][1])
        self.assertTrue(self.test.status in self.mock.messages[0][1])
        self.assertTrue(self.other_test.status in self.mock.messages[0][1])

    def test_load_other_when_both_have_modifications_no_differences(self):
        self.test.is_modified = True
        self.other_test.endtime = '20080101 10:10:10.100'
        self.mock.return_ = True
        self.assertFalse(self.test._load_other(self.other_test, self.mock.call),
                         'Message, status and tags are same, should not update items')
        self.assertEqual(len(self.mock.messages), 0)


class TestLoadOtherWithKeywords(_TestAddingData):

    def setUp(self):
        _TestAddingData.setUp(self)
        self.kw = self.test.keywords[0]
        self.other_kw = self.other_test.keywords[0]
        self.kw.is_modified = True
        self.other_kw.status = 'PASS'
        self.other_kw.message = 'working'
        self.other_kw.endtime = '20080101 10:10:10.100'
        self.mock = MockDialog()

    def test_load_other_with_keywords(self):
        self.assertTrue(self.kw._load_other(self.other_kw, self.mock.call))
        self.assertEqual(self.mock.messages[0],
                         self.kw._create_message_for_duplicate_results(self.other_kw))
        self.assertTrue('Status: PASS\n' in self.mock.messages[0][1])
        self.assertTrue('Message: working\n' in self.mock.messages[0][1])

    def test_load_other_with_keywords_only_message_different(self):
        self.other_kw.status = self.kw.status
        self.assertTrue(self.kw._load_other(self.other_kw, self.mock.call))
        self.assertTrue('Status: %s\n' % (self.kw.status) not in self.mock.messages[0][1])
        self.assertTrue('Message: working\n' in self.mock.messages[0][1])

    def test_load_other_with_keywords_having_same_data(self):
        self.other_kw.status = self.kw.status
        self.other_kw.message = self.kw.message
        self.assertFalse(self.kw._load_other(self.other_kw, self.mock.call),
                         'Message and status are same, should not update items')
        self.assertEqual(len(self.mock.messages), 0)


class TestGettingTags(unittest.TestCase):

    def setUp(self):
        data = normcase(join(dirname(__file__), 'data', 'root_suite'))
        self.suite = IO().load_data(data)

    def test_getting_tags_from_test_with_tags_and_tags_empty(self):
        test = self.suite.suites[0].tests[0]
        tags = []
        test.get_all_visible_tags(tags)
        self.assertEquals(['tag-1', 'tag-2', 'tag-3'], tags)

    def test_getting_tags_from_test_with_tags_and_some_tags(self):
        test = self.suite.suites[0].tests[0]
        tags = ['some', 'tag-2']
        test.get_all_visible_tags(tags)
        self.assertEquals(['some', 'tag-2', 'tag-1', 'tag-3'], tags)

    def test_getting_tags_from_test_without_tags_and_tags_empty(self):
        test = self.suite.suites[1].tests[0]
        tags = []
        test.get_all_visible_tags(tags)
        self.assertEquals([], tags)

    def test_getting_tags_from_test_without_tags_and_some_tags(self):
        test = self.suite.suites[1].tests[0]
        tags = ['some', 'tag-2']
        test.get_all_visible_tags(tags)
        self.assertEquals(['some', 'tag-2'], tags)

    def test_getting_tags_from_file_suite_with_tags_and_tags_empty(self):
        suite = self.suite.suites[0]
        tags = []
        suite.get_all_visible_tags(tags)
        self.assertEquals(['tag-1', 'tag-2', 'tag-3'], tags)

    def test_getting_tags_from_file_suite_with_tags_and_some_tags(self):
        suite = self.suite.suites[0]
        tags = ['some', 'tag-2']
        suite.get_all_visible_tags(tags)
        self.assertEquals(['some', 'tag-2', 'tag-1', 'tag-3'], tags)

    def test_getting_tags_from_file_suite_without_tags_and_tags_empty(self):
        suite = self.suite.suites[1]
        tags = []
        suite.get_all_visible_tags(tags)
        self.assertEquals([], tags)

    def test_getting_tags_from_file_suite_without_tags_and_some_tags(self):
        suite = self.suite.suites[1]
        tags = ['some', 'tag-2']
        suite.get_all_visible_tags(tags)
        self.assertEquals(['some', 'tag-2'], tags)

    def test_getting_tags_from_directory_suite(self):
        tags = self.suite.get_all_visible_tags()
        self.assertEquals(['tag-1', 'tag-2', 'tag-3'], tags)

class TestAbstractManualModel(_TestAddingData):

    def test_get_valid_time_with_robots_old_default_time(self):
        self.assertEquals(self.suite._get_valid_time('N/A'), model.EMPTY_TIME)
    
    def test_get_valid_time_with_mabots_old_default_time(self):
        self.assertEquals(self.suite._get_valid_time('00000000 00:00:00.000'), model.EMPTY_TIME)

    def test_get_valid_time_with_new_default_time(self):
        self.assertEquals(self.suite._get_valid_time('20000101 00:00:00.000'), model.EMPTY_TIME)

    def test_get_valid_time_with_too_short_value(self):
        self.assertEquals(self.suite._get_valid_time('20010101 00:00:00'), model.EMPTY_TIME)

    def test_get_valid_time_with_too_long_value(self):
        self.assertEquals(self.suite._get_valid_time('20010101 00:00:00.0000'), model.EMPTY_TIME)

    def test_get_valid_time_with_valid_value_is_not_changed(self):
        self.assertEquals(self.suite._get_valid_time('20111111 11:11:11.111'), '20111111 11:11:11.111')

    def test_testcase_multiline_documentation(self):
        expected = u'''\
long documentation line will be causing possible problems if we are not really really careful
new line which will have more information about everything

new paragraph'''
        self.assertEqual(self.suite.suites[0].tests[0].doc, expected)

class TestManualMessage(unittest.TestCase):

    def test_manual_message_default_timestamp(self):
        mm = ManualMessage('Mjaijai', 'PASS')
        self.assertNotEqual(mm.timestamp, '00000000 00:00:00.000')
        self.assertEqual(len(mm.timestamp), len('00000000 00:00:00.000'))

    def test_manual_message_fixes_invalid_timestamp(self):
        mm = ManualMessage('All your base are belong to us', 'FAIL', timestamp='00000000 00:00:00.000')
        self.assertNotEqual(mm.timestamp, '00000000 00:00:00.000')
        self.assertEqual(len(mm.timestamp), len('00000000 00:00:00.000'))


class MockDialog:

    def __init__(self):
        self.return_ = True
        self.messages = []

    def call(self, title, message):
        self.messages.append((title, message))
        return self.return_

if __name__ == "__main__":
    unittest.main()
