# -*- coding: UTF-8 -*-
from __future__ import division

import os
test_dir = os.path.dirname(__file__)
tmp_dir = os.path.join(test_dir, '.tmp')

import tempfile
from nose.plugins.skip import SkipTest


bin_path = os.path.join(test_dir, os.path.pardir, 'bin', 'pydflatex')

## mod_path = os.path.join(test_dir, os.path.pardir)
## import sys
## sys.path.insert(0, mod_path)
## print sys.path

from subprocess import Popen, PIPE

import re

import nose.tools as nt



from pydflatex import Typesetter, IsolatedTypesetter
from pydflatex.typesetter import LaTeXLogger, LaTeXLoggerColour, LaTeXError

try:
	import termcolor
except ImportError:
	colours = dict([(key, '') for key in LaTeXLoggerColour.colours])
else:
	colours = dict([(key,termcolor.colored('', **colargs)[:-4]) for key, colargs in LaTeXLoggerColour.colours.items()])

class Test_Output(object):

	def setUp(self):
		self.t = IsolatedTypesetter()
		self.t.clean_up_tmp_dir()
		self.setup_logger()

	def setup_logger(self):
		import logging
		self.logfile = tempfile.NamedTemporaryFile()
		self.handler = logging.FileHandler(self.logfile.name)
		self.t.setup_logger([self.handler])

	def tearDown(self):
		self.t.logger.removeHandler(self.handler)
		self.logfile.close()
		self.t.rm_tmp_dir()
		try:
			pdf_name = self.t.current_pdf_name
		except AttributeError:
			pass
		else:
			try:
				os.remove(pdf_name)
			except OSError:
				pass

## 	def mk_tmp(self, content):
## 		import tempfile
## 		f = tempfile.NamedTemporaryFile(suffix='.tex', dir=tmp_dir)
## 		f.write(content)
## 		return f
## 	
	def typeset(self, file_name, with_binary=False):
		if with_binary:
			self.output = Popen([bin_path, file_name], stderr=PIPE).communicate()[1]
		try:
			self.t.run(os.path.join(test_dir, 'latex', file_name))
		except Exception as e:
			raise e
		finally:
			self.output = self.logfile.read()

	def assert_contains(self, match, line=None, regexp=False):
		out = self.output
		if line is not None:
			out = out.splitlines()[line]
		if not regexp:
			does_match = out.find(match) != -1
		else:
			does_match = re.search(match, self.output, re.MULTILINE)
		if not does_match:
			raise AssertionError("'%s' not in\n%s" % (match, out))

	def assert_success(self):
		self.assert_contains('Typesetting of')
		self.assert_contains('completed')
		self.assert_contains(colours['success'])

	def test_simple(self):
		self.typeset('simple')
		self.assert_contains('pdflatex %s/latex/simple.tex' % test_dir, 0)
		self.assert_contains('Typeset', -1)
		self.assert_contains('This is pdfTeX', regexp=True)
		self.assert_contains(colours['success'])

	def test_error(self):
		try:
			self.typeset('error')
		except LaTeXError:
			pass
		self.assert_contains(r'%sUndefined control sequence \nonexistingmacro.' % colours['error'])

	def test_non_exist(self):
		self.typeset('nonexistent')
		self.assert_contains(colours['error'])
		self.assert_contains('File %s/latex/nonexistent.tex not found' % test_dir)

	def test_wrong_ext(self):
		self.typeset('simple.xxx')
		self.assert_contains('Wrong extension for %s/latex/simple.xxx' % test_dir)
		self.assert_contains(colours['error'])

	def test_trailing_dot(self):
		self.typeset('simple.')
		self.assert_success()

	def test_ref(self):
		self.typeset('ref')
		self.assert_contains("undefined")
		self.assert_contains("nonexistent")
		self.assert_contains('There were undefined references.', -2)
## 		self.assert_contains(ref_warning, -4)
		self.assert_contains(colours['error'], -2)

	def test_rerun(self):
		raise SkipTest('Rerun is broken')
		try:
			os.remove(os.path.join(test_dir, 'latex','rerun.aux'))
		except OSError:
			pass
		self.typeset('rerun')
		self.assert_contains('Rerun')
		self.assert_contains('[2] pdflatex ')
		self.assert_contains('\n%sLabel' % colours['warning'])
		self.assert_success

	def test_twice_label(self):
		self.typeset('twicelabel')
		self.assert_contains(colours['warning'],-3)
		self.assert_contains("Label `label' multiply defined", -3)
		self.assert_contains("There were multiply-defined labels", -2)
		self.assert_contains(colours['error'], -2)

	def test_cite(self):
		self.typeset('cite')
		self.assert_contains('citation')
		self.assert_contains(colours['error'])
## 	def test_no_tmp_dif(self):
## 		self.t.typeset_file('simple')

	def test_binary(self):
		self.typeset('simple', with_binary=True)
		self.assert_contains('pdflatex %s/latex/simple.tex' % test_dir, 0)

	def test_box(self):
		self.t.suppress_box_warning = False
		self.typeset('box')
		self.assert_contains('%sOverfull' % colours['box'])
		self.assert_contains('p.1')

	def test_nobox(self):
		self.typeset('box')
		nt.assert_equal(self.output.find('Overfull'), -1)

	def test_pdfsync(self):
		"""
		The auxiliary file pdfsync was moved to the current directory.
		"""
		aux = os.path.join(test_dir, 'latex','pdfsync.pdfsync')
		try:
			os.remove(aux)
		except OSError:
			pass
		self.typeset('pdfsync')
		nt.assert_true(os.path.exists(aux))

	def test_pdfrewritten(self):
		"""
		The pdf file is not moved, only rewritten in the same file.
		"""
		self.typeset('simple')
		inode = os.stat('simple.pdf').st_ino
		self.typeset('simple')
		new_inode = os.stat('simple.pdf').st_ino
		nt.assert_equal(inode, new_inode)

	def exists(self, file_name):
		return os.path.exists(os.path.join(test_dir, 'latex', file_name))

	def test_no_move_pdf_curdir(self):
		self.t.move_pdf_to_curdir = False
		self.typeset('simple')
		nt.assert_true(self.exists('simple.pdf'))

	def test_move_pdf_curdir(self):
		self.t.move_pdf_to_curdir = True # default
		self.typeset('simple')
		nt.assert_true(os.path.exists('simple.pdf'))

	def test_halt_on_error(self):
		self.t.halt_on_errors = True
		self.t.move_pdf_to_curdir = False
		try:
			self.typeset('continue')
		except LaTeXError:
			pass
		nt.assert_false(self.exists('continue.pdf'))

	def test_continue(self):
		self.t.halt_on_errors = False
		self.t.move_pdf_to_curdir = False
		self.typeset('continue')
		print os.path.exists('./.latex_tmp/continue.pdf')
		print os.path.exists('./latex/continue.pdf')
		nt.assert_true(self.exists('continue.pdf'))

	def test_nostyle(self):
		self.t.colour = False
		self.setup_logger()
		self.typeset('simple')
		self.assert_contains('^Typesetting', regexp=True)

