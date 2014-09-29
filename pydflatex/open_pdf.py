#!/usr/bin/env python
# coding: UTF-8
from __future__ import division

from processor import Processor
import os

class OpenPdf(Processor):
	def open_pdf(self, root):
		"""
		Open the generated pdf file.
		"""
		pdf_name = root + os.path.extsep + 'pdf'
		self.logger.info('Opening "{0}"...'.format(pdf_name))
		os.system('/usr/bin/open "{0}"'.format(pdf_name))


