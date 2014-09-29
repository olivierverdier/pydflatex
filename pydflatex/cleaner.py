#!/usr/bin/env python
# coding: UTF-8
from __future__ import division

import os
import subprocess

from processor import Processor

class Cleaner(Processor):
	"""
	Identify all the output files and make them invisible.
	"""
	defaults={}

	@classmethod
	def fls_file(self, file_base):
		return os.path.join(os.curdir, file_base+os.path.extsep+'fls')

	@classmethod
	def output_files(self, fls_file):
		"""
		Generate the paths of all the auxiliary files.
		"""
		yield fls_file
		with open(fls_file) as lines:
			for line in lines:
				if line[:6] == 'OUTPUT':
					aux_file = line[7:].rstrip()
					yield aux_file

	def make_invisible(self, base, aux_file):
		"""
		This is system dependent, so by default we don't do anything.
		"""
		pass

	def handle_aux(self, base, file_base):
		for aux_file in self.output_files(self.fls_file(file_base)):
			if os.path.splitext(aux_file)[1] != '.pdf':
				self.make_invisible(base, aux_file)

def make_invisible_darwin(self, base, aux_file):
	"""
	The Darwin specific version for making files invisible.
	"""
	cmd = ['SetFile', '-a', 'V']
	full_path = os.path.join(base, aux_file)
	try:
		subprocess.Popen(cmd + [full_path]).communicate()
	except OSError, e:
		self.logger.info("{0}\nInstall the Developer Tools if you want the auxiliary files to get invisible".format(e))

import platform
if platform.system() == 'Darwin':
	Cleaner.make_invisible = make_invisible_darwin
