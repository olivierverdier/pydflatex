#!/usr/bin/env python
# coding: UTF-8
from __future__ import division

import os

from processor import Processor

# loading the log parser
from pydflatex.latexlogparser import LogCheck

class LogProcessor(Processor):
	"""
	Process a log file.
	Options:
		- suppress_box_warning
	"""

	defaults = Processor.defaults.copy()
	defaults.update({
		'suppress_box_warning': True,
	})

	@classmethod
	def log_file_path(self, base, file_base):
		return os.path.join(base, file_base + os.path.extsep + 'log')

	@classmethod
	def parse_log(self, log_file_path):
		"""
		Parse log file
		"""
		parser = LogCheck()
		parser.read(log_file_path)
		return parser

	def process_log(self, log_file_path):
		"""
		Parse log and display corresponding info.
		"""
		parser = self.parse_log(log_file_path)

		# Process info from parser
		error = self.process_parser(parser)
		return error

	def process_boxes(self, boxes):
		for box in boxes:
			has_occ = box['text'].find(r' has occurred while \output is active')
			if has_occ != -1:
				box['text'] = box['text'][:has_occ]
			if not self.options['suppress_box_warning']:
				self.logger.box_warning(box)

	def process_references(self, references):
		for ref in references:
			self.logger.ref_warning(ref)

	def process_warnings(self, warnings):
		for warning in warnings:
			# following should be filtered via the loggers filter!
			if warning.get('pkg') == 'hyperref' and warning['text'].find('Token') != -1:
				continue # I hate those hyperref warning
			if warning.get('text') == r'Command \centerline is TeX.  Use \centering or center environment instead.':
				continue # warning from the nag package
			self.logger.latex_warning(warning)

	def process_parser(self, parser):
		"""
		Process information from the parser and print out the gist of it.
		"""
		self.process_boxes(parser.get_boxes())
		self.process_references(parser.get_references())
		self.process_warnings(parser.get_warnings())
		errors = list(parser.get_errors())
		if errors:
			for error in errors:
				self.logger.latex_error(error)
			return errors[0]

