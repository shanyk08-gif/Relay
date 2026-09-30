import subprocess
import unittest
from unittest.mock import patch
from start_gemini import load_key


def result(code=0, text=''):
    return subprocess.CompletedProcess([], code, stdout=text, stderr='')


class KeychainStartupTest(unittest.TestCase):
    @patch('start_gemini.subprocess.run')
    def test_reuses_key_without_setup(self, run):
        run.return_value = result(text='test-key\n')
        self.assertEqual(load_key(), 'test-key')
        self.assertEqual(run.call_count, 1)

    @patch('start_gemini.subprocess.run')
    def test_first_setup_uses_native_hidden_prompt(self, run):
        run.side_effect = [result(44), result(), result(text='test-key\n')]
        self.assertEqual(load_key(), 'test-key')
        command = run.call_args_list[1].args[0]
        self.assertEqual(command[1], 'add-generic-password')
        self.assertEqual(command[-1], '-w')
        self.assertNotIn('test-key', str(run.call_args_list))

    @patch('start_gemini.subprocess.run')
    def test_access_denied_does_not_overwrite(self, run):
        run.return_value = result(36)
        with self.assertRaises(SystemExit):
            load_key()
        self.assertEqual(run.call_count, 1)

    @patch('start_gemini.subprocess.run')
    def test_cancelled_save_stops_startup(self, run):
        run.side_effect = [result(44), result(1)]
        with self.assertRaises(SystemExit):
            load_key()
        self.assertEqual(run.call_count, 2)


if __name__ == '__main__':
    unittest.main()
