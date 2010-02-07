# -*- coding: UTF-8 -*-
from __future__ import division

import os
root = os.path.dirname(__file__)
tmp_dir = os.path.join(root, '.tmp')

from subprocess import Popen, PIPE

import re

import nose.tools as nt

success = '\x1B[32;01m'
failure = '\x1B[31;01m'
ref_warning = "\x1B[35;01m"
warning = '\x1B[35;01m'

class Test_Output(object):
	
	def setUp(self):
		from pydflatex import Typesetter
		self.t = Typesetter()
		self.t.rm_tmp_dir()
	
## 	def mk_tmp(self, content):
## 		import tempfile
## 		f = tempfile.NamedTemporaryFile(suffix='.tex', dir=tmp_dir)
## 		f.write(content)
## 		return f
## 	
	def typeset(self, file_name):
		self.output = Popen(['pydflatex', file_name], stderr=PIPE).communicate()[1]

	def assert_contains(self, match, line=None):
## 		does_match = re.search(match, self.output)
		out = self.output
		if line is not None:
			out = out.splitlines()[line]
		does_match = out.find(match) != -1
		if not does_match:
			raise AssertionError("'%s' not in\n%s" % (match, out))
	
	def assert_success(self):
		self.assert_contains('Typesetting of')
		self.assert_contains('completed')
		self.assert_contains(success)
			
	def test_simple(self):
		self.typeset('simple')
		self.assert_contains('Typesetting simple.tex', 0)
		self.assert_contains('Typeset', -1)
		self.assert_contains(success)
	
	def test_error(self):
		self.typeset('error')
		self.assert_contains(r'3: Undefined control sequence \nonexistingmacro.')
		self.assert_contains(failure)
	
	def test_non_exist(self):
		self.typeset('nonexistent')
		self.assert_contains(failure)
		self.assert_contains('File nonexistent.tex not found')
	
	def test_wrong_ext(self):
		self.typeset('simple.xxx')
		self.assert_contains('Wrong extension for simple.xxx')
		self.assert_contains(failure)
	
	def test_trailing_dot(self):
		self.typeset('simple.')
		self.assert_success()
	
	def test_ref(self):
		self.typeset('ref')
		self.assert_contains("undefined")
		self.assert_contains("nonexistent")
		self.assert_contains('There were undefined references.', -2)
## 		self.assert_contains(ref_warning, -4)
		self.assert_contains(warning, -2)
	
	def test_rerun(self):
		self.typeset('rerun')
		self.assert_contains('Rerun')
		self.assert_contains('pdflatex run number 2')
		self.assert_success
	
	def test_twice_label(self):
		self.typeset('twicelabel')
		self.assert_contains(warning,-2)
		self.assert_contains(warning,-3)
		self.assert_contains("Label `label' multiply defined", -3)
		self.assert_contains("There were multiply-defined labels", -2)
	
## 	def test_no_tmp_dif(self):
## 		self.t.typeset_file('simple')
	