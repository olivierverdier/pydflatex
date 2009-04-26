#!/usr/bin/env python
# (c) Olivier Verdier <olivier.verdier@gmail.com>, 2007-2009
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

stream = sys.stdout

# message print
flags = {'E': "\x1B[01;31m", 'no':'', 'G': "\x1B[01;32m", 'W': "\x1B[01;33m", 'B': "\x1B[00;36m", 'R': "\x1B[01;35m", 'M': "\x1B[03;00m"}
def eprint(msg='', flag='no'):
	print >> stream, flags[flag],
	print >> stream, msg,
	print >> stream, "\x1B[00;00m"

class Typesetter(object):
	def __init__(self, **options):
		# storing the options
		for k, v in options.items():
			self.__setattr__(k,v)
		# loading the log parser
		from pydflatex.latexlogparser import LogCheck
		self.parser = LogCheck()
		self.tmp_dir = self.create_tmp_dir(os.path.curdir)

	# maximum number of pdflatex runs
	max_run = 5
	
	tmp_dir_name = '.latex_tmp'
	
	halt_on_errors = True
	
	open = False
	
	clean_up = False
	
	extra_run = False
	
	# whereas the pdf file produced will be pulled back in the current directory
	move_pdf_to_curdir = True
	
	new_pdf_name = ''
	
	suppress_warning = False

	# extensions of the files that will be "pulled back" to the directory where the file is
	# on Mac OS X those files will be set invisible
	move_exts = ['pdfsync','pdf']

	
	def create_tmp_dir(self, base):
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
	
	def run(self, file_paths):
		"""
		Compile several files at once
		"""
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
			if not self.suppress_warning:
				eprint("%4s: %s" % (box.get('page', ''), box['text']), 'B')
		for ref in parser.get_references():
			eprint("%4s: %s" % (ref.get('line',''), ref['text']), 'R')
		for warning in parser.get_warnings():
			if warning.get('pkg') == 'hyperref' and warning['text'].find('Token') != -1:
				continue # I hate those hyperref warning
			package = warning.get('pkg', '')
			if package:
				package = ' [%s]' % package
			eprint("%4s:%s %s" % (warning.get('line',''), package, warning['text']), 'W')
		eprint()
		for error in parser.get_errors():
			eprint("%s %4s: %s" % (error['file'], error.get('line',''), error['text']), 'E')
			if error.get('code'): # if the code is available we print it:
				eprint("%4s:\t %s" % (error.get('line',''), error['code']))
	
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
				
				shutil.move(os.path.join(self.tmp_dir, aux_name), dest)
				final_path = os.path.join(dest, aux_name)
				if os.uname()[0] == 'Darwin': # on Mac OS X we hide all moved files...
					if aux_ext != 'pdf': # ...except the pdf
						if os.system('/Developer/Tools/SetFile -a V %s' % final_path):
							eprint("Install the Developer Tools if you want the auxiliary files to get invisible", 'W')
					elif self.open:
						eprint('Opening "%s"...' % pdf_name)
						os.system('/usr/bin/open "%s"' % pdf_name)						

			except IOError:
				if aux_ext == 'pdf':
					message = 'pdf file "%s" not found.' % aux_name
					eprint('\n\t%s' % message, 'E')
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
				eprint("Wrong extension for %s" % tex_path, 'E')
				return
			else:
				full_path = tex_path
		else:
			full_path = root + os.path.extsep + 'tex'
		
		# make sure that the file exists
		if not os.path.exists(full_path):
			eprint('File %s not found' % full_path, 'E')
			return


		# log file
		log_file = os.path.join(self.tmp_dir, file_base + os.path.extsep + 'log')

		eprint('Typesetting %s\n' % full_path)
		
		# preparing the extra run slot
		self.extra_run_slot = extra_run
		
		for run_nb in range(self.max_run):
			# run pdflatex
			eprint("\n\tpdflatex run number %d\n" % (run_nb + 1))
			os.popen('pdflatex --shell-escape -no-mktex=pk %s	 -interaction=batchmode --output-directory=%s %s' % (["", "-halt-on-error"][self.halt_on_errors], self.tmp_dir, root))
			try:
				self.parse_log(log_file)
			except KeyboardInterrupt:
				eprint ("Keyboard Interruption", 'E')
				sys.exit()
			except IOError: # if the file is invalid or doesn't exist
				eprint("Log file not found")
			except ValueError:
				eprint("Wrong format of the log file")
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
		eprint('Typesetting of "%s" completed in %ds.' % (full_path, int(time_end - time_start)), 'G')
		if self.clean_up:
			shutil.rmtree(self.tmp_dir)