#!/usr/bin/env python
# (c) Olivier Verdier <olivier.verdier@gmail.com>, 2007-2010
"""
A wrapper around pdflatex to allow:
- hiding of the temporary files in various ways
- running pdflatex blazingly fast using the -batchmode option
	and returning feedback by parsing the log file.
"""

import os
import sys
import shutil
import time


import logging
try:
	from termcolor import colored
except ImportError:
	import warnings
	warnings.warn('termcolor was not found: in black and white it will be')
	def colored(msg, *args, **kwargs):
		return msg

class LaTeXLogger(logging.Logger):
	line_template = 'L%-5s'
	page_template = 'p.%-4s'
	package_template = '[%s]'
	head_template = '%s%s%s: '
	
	colours = {
	 	'success': {'color': 'green', 'attrs':['bold']},
		'error' : {'color': 'red', 'attrs': ['bold']},
		'ref_warning' : {'color': 'red', 'attrs':['bold']},
		'warning' : {'color': 'magenta'},
		'box' : {'color': 'cyan'},
		'info': {'attrs': ['bold']}
		}
	
	def box(self, page, msg):
		"""
		Box (over/underfull) warnings.
		"""
		head = ''
		if page:
			head += self.page_template % page
		self.info(colored('%s: %s' % (head, msg), **self.colours['box']))
	
	def warning(self, msg):
		"""
		LaTeX warning
		"""
		logging.Logger.warning(self, msg)
	
	def get_page_line(self, info):
		"""
		Extract the page and line information and formats it.
		"""
		line_str = ''
		line = info.get('line','')
		page = info.get('page','')
		if line:
			line_str += self.line_template % line
		page_str = ''
		if page:
			page_str += self.page_template % page
		package_str = ''
		package = info.get('pkg')
		if package:
			package_str += self.package_template % package
		if line_str or page_str:
			return self.head_template % (package_str, page_str, line_str)
		return ''
			
	
	def latex_warning(self, warning):
		"""
		Extract the info from the `warning` object.
		"""
		msg = warning['text']
		if msg == 'There were undefined references.':
			return self.error(msg)
		head = self.get_page_line(warning)
		msg = '%s%s' % (head, colored(msg, **self.colours['warning']))
		self.warning(msg)
	
	def latex_error(self, error):
		self.error("%s:%s: %s" % (error['file'], error.get('line',''), error['text']))
		if error.get('code'): # if the code is available we print it:
			self.error("%4s:\t %s" % (error.get('line',''), error['code']))

	def error(self, msg):
		"""
		Error (coloured)
		"""
		logging.Logger.error(self, colored(msg, **self.colours['error']))
	
	def success(self, msg):
		"""
		Success (coloured)
		"""
		self.info(colored(msg, **self.colours['success']))
	
	def ref_warning(self, ref):
		"""
		Special format for citation and reference warnings.
		"""
		head = self.get_page_line(ref)
		undefined = ref.get('ref','')
		citation = ref.get('cite', '')
		if undefined:
			self.info("%s'%s' %s" % (head, colored(undefined, **self.colours['ref_warning']), 'undefined'))
		elif citation:
			self.info("%s[%s] %s" % (head, colored(citation, **self.colours['ref_warning']), 'undefined'))
		else:
			self.latex_warning(ref)
	
	def message(self, msg):
		"""
		Messages in bold
		"""
		self.info(colored(msg, **self.colours['info']))
	


stderr_logger = LaTeXLogger('pydflatex')
stderr_logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

## formatter = logging.Formatter('%(message)s')
## handler.setFormatter(formatter)

stderr_logger.addHandler(handler)

	
class Typesetter(object):
	def __init__(self, **options):
		# storing the options
		for k, v in options.items():
			self.__setattr__(k,v)
		# loading the log parser
		from pydflatex.latexlogparser import LogCheck
		self.parser = LogCheck()
		self.tmp_dir = self.create_tmp_dir()

	# maximum number of pdflatex runs
	max_run = 5
	
	logger = stderr_logger
	
	tmp_dir_name = '.latex_tmp'
	
	halt_on_errors = True
	
	open_pdf = False
	
	clean_up = False
	
	extra_run = False
	
	# whereas the pdf file produced will be pulled back in the current directory
	move_pdf_to_curdir = True
	
	new_pdf_name = ''
	
	suppress_box_warning = False

	# extensions of the files that will be "pulled back" to the directory where the file is
	# on Mac OS X those files will be set invisible
	move_exts = ['pdfsync','pdf']

	
	def create_tmp_dir(self, base=os.path.curdir):
		"""
		Create the temporary directory if it doesn't exist
		return the tmp_dir
		"""
		tmp_dir = os.path.join(base, self.tmp_dir_name)
		if not os.path.isdir(tmp_dir):
			try:
				os.mkdir(tmp_dir)
			except OSError:
				raise IOError('A file named "%s" already exists in this catalog' % tmp_dir)
		return tmp_dir
	
	def rm_tmp_dir(self):
		"""
		Remove the temporary dir. Useful for testing purposes.
		"""
		shutil.rmtree(self.tmp_dir)
	
	def clean_up_tmp_dir(self):
		"""
		Cleans up the tmp dir, i.e., deletes it and create a new pristine one.
		"""
		self.rm_tmp_dir()
		self.create_tmp_dir()

	
	def run(self, file_paths):
		"""
		Compile several files at once
		"""
		# clean up first if needed
		if self.clean_up:
			self.clean_up_tmp_dir()
		# easier to write with one file
		if not isinstance(file_paths, (list, tuple)):
			file_paths = [file_paths]
		for tex_path in file_paths:
			self.typeset_file(tex_path)
	
	def parse_log(self, log_file):
		"""
		Read the log file and print out the gist of it.
		"""
		parser = self.parser
		parser.read(log_file)
		for box in parser.get_boxes():
			has_occ = box['text'].find(r' has occurred while \output is active')
			if has_occ != -1:
				box['text'] = box['text'][:has_occ]
			if not self.suppress_box_warning:
				self.logger.box(box.get('page'), box['text'])
		for ref in parser.get_references():
			self.logger.ref_warning(ref)
		for warning in parser.get_warnings():
			# following should be filtered via the loggers filter!
			if warning.get('pkg') == 'hyperref' and warning['text'].find('Token') != -1:
				continue # I hate those hyperref warning
			self.logger.latex_warning(warning)
		for error in parser.get_errors():
			self.logger.latex_error(error)
	
	def move_auxiliary(self, base, file_base):
		"""
		Move some auxiliary files back to the tex directory
		"""
		for aux_ext in self.move_exts:
			aux_name = file_base + os.path.extsep + aux_ext
			try:
				dest = os.path.join(base,os.curdir)
				# we move the pdf in the current directory
				if aux_ext == 'pdf':
					pdf_name = os.path.join(base, aux_name)
					if self.move_pdf_to_curdir:
						dest = os.curdir
						pdf_name = aux_name
					if self.new_pdf_name:
						dest = os.path.join(dest,self.new_pdf_name + os.path.extsep + 'pdf')
						pdf_name = dest
					# store the pdf name for later use
					self.current_pdf_name = pdf_name
				
				shutil.move(os.path.join(self.tmp_dir, aux_name), dest)
				final_path = os.path.join(dest, aux_name)
				if os.uname()[0] == 'Darwin': # on Mac OS X we hide all moved files...
					if aux_ext != 'pdf': # ...except the pdf
						if os.system('/Developer/Tools/SetFile -a V %s' % final_path):
							self.logger.info("Install the Developer Tools if you want the auxiliary files to get invisible")

			except IOError:
				if aux_ext == 'pdf':
					message = 'pdf file "%s" not found.' % aux_name
## 					self.logger.error('\n\t%s' % message)
					raise IOError(message)


	def typeset_file(self, tex_path, extra_run=None):
		"""
		Typeset one given file.
		"""
		if extra_run is None:
			extra_run = self.extra_run
		time_start = time.time()
		# find out the directory where the file is
		base,file_name = os.path.split(tex_path)
		file_base, file_ext = os.path.splitext(file_name)
		# setup the TEXINPUTS variable
		os.environ['TEXINPUTS'] = base + ':'
		# find out the name of the file to compile
		root, file_ext = os.path.splitext(tex_path)
		if file_ext[1:]:
			if file_ext[1:] != 'tex':
				self.logger.error("Wrong extension for %s" % tex_path)
				return
			else:
				full_path = tex_path
		else:
			full_path = root + os.path.extsep + 'tex'
		
		# make sure that the file exists
		if not os.path.exists(full_path):
			self.logger.error('File %s not found' % full_path)
			return


		# log file
		log_file = os.path.join(self.tmp_dir, file_base + os.path.extsep + 'log')

		self.logger.info('Typesetting %s\n' % full_path)
		
		# preparing the extra run slot
		self.extra_run_slot = extra_run
		
		for run_nb in range(self.max_run):
			# run pdflatex
			self.logger.message("pdflatex run number %d" % (run_nb + 1))
			command = 'pdflatex -etex -no-mktex=pk %s	-interaction=batchmode --output-directory=%s %s' % (["", "-halt-on-error"][self.halt_on_errors], self.tmp_dir, root)
			self.logger.debug(command)
			os.popen(command)
			try:
				self.parse_log(log_file)
			except KeyboardInterrupt:
				self.logger.error("Keyboard Interruption")
				sys.exit()
			except IOError: # if the file is invalid or doesn't exist
				self.logger.error("Log file not found")
			except ValueError:
				self.logger.error("Wrong format of the log file")
				break # stop processing this file
			else:
				self.move_auxiliary(base,file_base)
				# we stop on errors or if no other run is needed
				if not self.parser.run_needed() or self.parser.errors():
					if self.extra_run_slot > 0: # run some more times
						self.extra_run_slot -= 1
					else:
						break

		time_end = time.time()
		self.logger.success('Typesetting of "%s" completed in %ds.' % (full_path, int(time_end - time_start)))
		if self.open_pdf:
			self.logger.info('Opening "%s"...' % self.current_pdf_name)
			os.system('/usr/bin/open "%s"' % self.current_pdf_name)
