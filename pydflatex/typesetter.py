#!/usr/bin/env python

import subprocess
import datetime

from processor import Processor

class Typesetter(Processor):
	"""
	Typeset a TeX file.
	Options:
		- halt_on_errors
		- xetex
	"""

	defaults = Processor.defaults.copy()
	defaults.update({
			'halt_on_errors': True,
			'xetex': False,
			})

	def engine(self):
		return ['pdflatex','xelatex'][self.options['xetex']]

	def arguments(self):
		"""
		Arguments to the (pdf|xe)latex command.
		"""
		args = [self.engine(),
				'-8bit',
				'-no-mktex=pk',
				'-interaction=batchmode',
				'-recorder',
				]
		if self.options['halt_on_errors']:
			args.insert(-1, '-halt-on-error')
		return args

	def typeset(self, full_path, ):
		"""
		Typeset one given file.
		"""
		# run pdflatex
		now = datetime.datetime.now().strftime('%Y-%m-%d %H.%M.%S')
		self.logger.message("\t[{now}] {engine} {file}".format(engine=self.engine(), file=full_path, now=now))
		arguments = self.arguments()
		# append file name
		arguments.append(full_path)
		self.logger.debug("\n"+" ".join(arguments)+"\n")
		output = subprocess.Popen(arguments, stdout=subprocess.PIPE).communicate()[0]
		self.logger.message(output.splitlines()[0])


