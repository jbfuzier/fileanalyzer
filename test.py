__author__ = 'jb'

import unittest
from Tools.tools import hashdigest
from StringIO import StringIO
from Model import Submission


class TestTools(unittest.TestCase):

    def setUp(self):
        pass

    def test_hashdigest(self):
        stream = StringIO("The quick brown fox jumps over the lazy dog")
        r = hashdigest("Tools\exiftool.py")
        self.assertEqual(r['md5'], "b5504d2e2cb89f1883d8d9736c67b87c")
        self.assertEqual(r['sha1'], "f74f2998f8f24bfa71292d0b4d492ce245d4b0e9")
        self.assertEqual(r['sha256'], "abfcccf9d3db8eeca9e35e3854f0b2262563c778754a573fb1d92010e36345ba")

    def test_newsubmission(self):
        f = Submission("c:\\windows\\system32\\calc.exe")
        self.assertEqual(f.file.md5, "60b7c0fead45f2066e5b805a91f4f0fc")
        self.assertEqual(f.file.type, "Win32 EXE")
        self.assertEqual(f.file.mimetype, "application/octet-stream")
        self.assertEqual(f.extension, "exe")
        self.assertEqual(f.name, "calc.exe")
