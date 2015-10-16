#!/usr/bin/env python
# coding: UTF-8
from __future__ import division

import logging

class LaTeXLogger(logging.Logger):
	line_template = 'L{0:5}'
	page_template = 'p.{0:4}'
	package_template = '[{0}]'
	head_template = '{package}{page}{line}: '

	def styled(self, msg, style):
		return msg

	def box_warning(self, info):
		"""
		Box (over/underfull) warnings.
		"""
		head = self.get_page_line(info)
		msg = info['text']
		self.info('{head}{message}'.format(head=head, message=self.styled(msg,'box')))

	def warning(self, msg):
		"""
		LaTeX warning
		"""
		logging.Logger.warning(self, msg)

	def get_page_line(self, info):
		"""
		Extract the page and line information and formats it.
		"""
		line = info.get('line','')
		page = info.get('page','')
		line_str = self.line_template.format(line)
		page_str = self.page_template.format(str(page).strip())
		package = info.get('pkg','')
		package_str = self.package_template.format(package) and package
		if line_str or page_str:
			return self.head_template.format(package=package_str, page=page_str, line=line_str)
		return ''


	def latex_warning(self, warning):
		"""
		Extract the info from the `warning` object.
		"""
		msg = warning['text']
		if msg.find('There were') == 0: # for ['There were undefined references.', 'There were multiply-defined labels.']
			return self.error(msg)
		if msg.find('Rerun to get cross-references right.'):
			return self.warning(self.styled(msg,'warning'))
		head = self.get_page_line(warning)
		msg = '{head}{warning}'.format(head=head, warning=self.styled(msg,'warning'))
		self.warning(msg)

	def latex_error(self, error):
		logging.Logger.error(self, "{file}:{line}: {error}".format(file=error['file'], line=error.get('line',''), error=self.styled(error['text'],'error')))
		if error.get('code'): # if the code is available we print it:
			self.message("{line}:\t {code}".format(line=self.line_template.format(error.get('line','')), code=error['code']))

	def error(self, msg):
		"""
		Error (coloured)
		"""
		logging.Logger.error(self, self.styled(msg,'error'))

	def success(self, msg):
		"""
		Success (coloured)
		"""
		self.info(self.styled(msg,'success'))

	def ref_warning(self, ref):
		"""
		Special format for citation and reference warnings.
		"""
		head = self.get_page_line(ref)
		undefined = ref.get('ref','')
		citation = ref.get('cite', '')
		if undefined:
			self.info("{head}'{reference}' {undefined}".format(head=head, reference=self.styled(undefined,'ref_warning'), undefined='undefined'))
		elif citation:
			self.info("{head}[{citation}] {undefined}".format(head=head, citation=self.styled(citation,'ref_warning'), undefined='undefined'))
		else:
			self.latex_warning(ref)

	def message(self, msg):
		"""
		Messages in bold
		"""
		self.info(self.styled(msg,'info'))



class LaTeXLoggerColour(LaTeXLogger):
	"""
	Logger using ascii colour escape codes (suitable for terminal)
	"""
	colours = {
		'success': {'color': 'green', 'attrs':['bold']},
		'error' : {'color': 'red', 'attrs': ['bold']},
		'ref_warning' : {'color': 'red', 'attrs':['bold']},
		'warning' : {'color': 'magenta'},
		'box' : {'color': 'cyan'},
		'info': {'attrs': ['bold']}
		}

	@classmethod
	def styled(self, msg, style):
		style_specs = self.colours[style]
		color = style_specs.get('color')
		styled = ''
		if color:
			styled += getattr(terminal, style_specs['color'])
		for attr in style_specs.get('attrs', []):
			styled += getattr(terminal, attr)
		styled += msg
		styled += terminal.normal
		return styled

try:
	import blessings
	terminal = blessings.Terminal()
except ImportError:
	import warnings
	warnings.warn('termstyle was not found: in black and white it will be')
	LaTeXLoggerColour = LaTeXLogger

latex_logger = LaTeXLogger('pydflatex')
latex_logger.setLevel(logging.DEBUG)

std_handler = logging.StreamHandler()
std_handler.setLevel(logging.INFO)

debug_handler = logging.StreamHandler()
debug_handler.setLevel(logging.DEBUG)

## formatter = logging.Formatter('%(message)s')
## handler.setFormatter(formatter)
