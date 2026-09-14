import shlex
import unittest
from unittest.mock import patch

import shortcuts


class WtypeTests(unittest.TestCase):
    def command(self, shortcut):
        with patch('shortcuts.shutil.which', return_value='/usr/bin/wtype'):
            return shortcuts.wtype_command(shortcut)[1:]

    def test_chords(self):
        for text in ('Super + Shift + F', 'super+shift+f', ' Super  +  Shift + F '):
            with self.subTest(text=text):
                self.assertEqual(self.command(text),
                                 ['-M', 'logo', '-M', 'shift', '-k', 'f',
                                  '-m', 'shift', '-m', 'logo'])

    def test_modifier_aliases_and_duplicates(self):
        for text, name in [('Control', 'ctrl'), ('Meta', 'logo'), ('Win', 'logo'),
                           ('Mod4', 'logo'), ('Alt', 'alt'), ('Mod1', 'alt'),
                           ('AltGr', 'altgr'), ('ISO_Level3_Shift', 'altgr'),
                           ('Caps Lock', 'capslock')]:
            with self.subTest(text=text):
                self.assertEqual(self.command(f'{text}+{text}+A'),
                                 ['-M', name, '-k', 'a', '-m', name])

    def test_keys(self):
        for text, key in [('Enter', 'Return'), ('eSc', 'Escape'), ('Space', 'space'),
                          ('Left', 'Left'), ('Page Down', 'Page_Down'),
                          ('page_up', 'Page_Up'), ('Backspace', 'BackSpace'),
                          ('Del', 'Delete'), ('PrintScreen', 'Print'), ('f5', 'F5'),
                          ('KP_Enter', 'KP_Enter'), ('XF86AudioMute', 'XF86AudioMute'),
                          ('+', 'plus'), ('-', 'minus'), (';', 'semicolon')]:
            with self.subTest(text=text):
                self.assertEqual(self.command(text), ['-k', key])
        for text in ('Ctrl++', 'Ctrl + +', 'Ctrl + plus'):
            self.assertEqual(self.command(text), ['-M', 'ctrl', '-k', 'plus', '-m', 'ctrl'])

    def test_invalid_input(self):
        for text in ('', ' ', 'Ctrl+', '+F', 'Ctrl++F', 'Hyper+F', 'Ctrl+bad key'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.command(text)
        with patch('shortcuts.shutil.which', return_value=None):
            with self.assertRaises(RuntimeError):
                shortcuts.wtype_command('Ctrl+C')

    def test_delayed_execution(self):
        with patch('shortcuts.shutil.which', return_value='/usr/bin/wtype'), \
             patch('shortcuts.subprocess.Popen') as popen:
            self.assertEqual(shortcuts.run_shortcut('Ctrl+C'), 0)
        args, kwargs = popen.call_args
        self.assertEqual(shlex.split(args[0][2].split('; exec ', 1)[1]),
                         ['/usr/bin/wtype', '-M', 'ctrl', '-k', 'c', '-m', 'ctrl'])
        self.assertTrue(args[0][2].startswith('sleep 0.15;'))
        self.assertTrue(kwargs['start_new_session'])
        with patch('shortcuts.subprocess.Popen') as popen:
            self.assertEqual(shortcuts.run_shortcut('Hyper+F'), 1)
            popen.assert_not_called()


if __name__ == '__main__':
    unittest.main()
