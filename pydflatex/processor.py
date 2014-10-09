#!/usr/bin/env python
# coding: UTF-8
from __future__ import division


import latex_logger

class Processor(object):
	"""
	Models an object with a logger and some options.
	General options:
		- colour
		- debug
	"""

	def __init__(self, logger=None, options=None):
		# storing the options
		self.options = self.defaults.copy()
		if options is not None:
			self.options.update(options)
		# setting up the logger
		if logger is not None:
			self.logger = logger
		else:
			self.logger = self.setup_logger()
		self.logger.debug("%s\ninitialized with\n%s\n" % (type(self), options))

	defaults={
			'colour': True,
			'debug': False,
			}

	def setup_logger(self, handlers=None):
		if self.options['colour']:
			LoggerClass = latex_logger.LaTeXLoggerColour
		else:
			LoggerClass = latex_logger.LaTeXLogger
		logger = LoggerClass('pydflatex')
		if not handlers:
			if not self.options['debug']:
				logger.addHandler(latex_logger.std_handler)
			else:
				logger.addHandler(latex_logger.debug_handler)
		else:
			for handler in handlers:
				logger.addHandler(handler)
		return logger


