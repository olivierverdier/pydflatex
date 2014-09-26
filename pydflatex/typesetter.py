#!/usr/bin/env python
# (c) Olivier Verdier <olivier.verdier@gmail.com>, 2007-2013
"""
A wrapper around pdflatex which
- runs pdflatex blazingly fast using the -batchmode option
- returns feedback by parsing the log file
- hides the temporary files in various ways
- opens the pdf file if needed
"""

import os
import shutil
import datetime
import time

import subprocess

# loading the log parser
from pydflatex.latexlogparser import LogCheck

import latex_logger as logger


class LaTeXError(Exception):
	"""
	LaTeX Error
	"""

class Typesetter(object):
	def __init__(self, tex_path=None, **options):
		self.tex_path = tex_path
		# storing the options
		for k, v in options.items():
			setattr(self, k, v)
		# setting up the logger
		self.setup_logger()
		self.logger.debug(options)

	colour = True
	debug = False

	def setup_logger(self, handlers=None):
		if self.colour:
			LoggerClass = logger.LaTeXLoggerColour
		else:
			LoggerClass = logger.LaTeXLogger
		self.logger = LoggerClass('pydflatex')
		if not handlers:
			if not self.debug:
				self.logger.addHandler(logger.std_handler)
			else:
				self.logger.addHandler(logger.debug_handler)
		else:
			for handler in handlers:
				self.logger.addHandler(handler)


	@classmethod
	def paths(self, tex_path):
		"""
		Figure out useful paths from the tex_path, and make sure that extension is tex.
		For tex_path = path/to/file.tex, or path/to/file we get
		base: path/to
		file_base: file
		root: path/to/file
		full_path: path/to/file.tex
		"""
		# find out the directory where the file is
		base, file_name = os.path.split(tex_path)
		file_base, file_ext = os.path.splitext(file_name)
		# setup the TEXINPUTS variable
		os.environ['TEXINPUTS'] = base + ':'
		# find out the name of the file to compile
		root, file_ext = os.path.splitext(tex_path)
		if file_ext[1:]:
			if file_ext[1:] != 'tex':
				raise LaTeXError("Wrong extension for {0}".format(tex_path))
			else:
				full_path = tex_path
		else:
			full_path = root + os.path.extsep + 'tex'
		# make sure that the file exists
		if not os.path.exists(full_path):
			raise LaTeXError('File {0} not found'.format(full_path))
		return {'base':base, 'file_base':file_base, 'root':root, 'full_path':full_path}


	def prepare(self, tex_path=None):
		if tex_path is None:
			tex_path = self.tex_path
		paths = self.paths(tex_path)
		return tex_path, paths

	typesetting = True
	log_parsing = True
	open_after = False

	def run(self, tex_path=None):
		"""
		Compile the current tex file.
		"""
		tex_path, paths = self.prepare(tex_path)

		full_path = paths['full_path']

		if self.typesetting:
			# Typeset
			time_start = time.time()
			self.typeset(full_path)
			time_end = time.time()
			success_message = 'Typesetting of "{name}" completed in {time:.1f}s.'.format(name=full_path, time=(time_end - time_start))


		if self.log_parsing:
			# Parse log
			log_file_path = self.log_file_path(paths['base'], paths['file_base'])
			self.process_log(log_file_path)

		if self.typesetting:
			# Print success message
			self.logger.success(success_message)

			# Post process
			self.handle_aux(paths['base'], paths['file_base'])
			if self.open_after:
				self.open_pdf(paths['root'])

	# Typesetting

	halt_on_errors = True
	xetex = False

	def engine(self):
		return ['pdflatex','xelatex'][self.xetex]

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
		if self.halt_on_errors:
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
		self.logger.debug(arguments)
		output = subprocess.Popen(arguments, stdout=subprocess.PIPE).communicate()[0]
		self.logger.message(output.splitlines()[0])

	# Log parsing

	suppress_box_warning = True

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
		if error and self.halt_on_errors:
			raise LaTeXError(error.get('text'))

	def process_parser(self, parser):
		"""
		Process information from the parser and print out the gist of it.
		"""
		for box in parser.get_boxes():
			has_occ = box['text'].find(r' has occurred while \output is active')
			if has_occ != -1:
				box['text'] = box['text'][:has_occ]
			if not self.suppress_box_warning:
				self.logger.box_warning(box)
		for ref in parser.get_references():
			self.logger.ref_warning(ref)
		for warning in parser.get_warnings():
			# following should be filtered via the loggers filter!
			if warning.get('pkg') == 'hyperref' and warning['text'].find('Token') != -1:
				continue # I hate those hyperref warning
			if warning.get('text') == r'Command \centerline is TeX.  Use \centering or center environment instead.':
				continue # warning from the nag package
			self.logger.latex_warning(warning)
		errors = list(parser.get_errors())
		if errors:
			for error in errors:
				self.logger.latex_error(error)
			return errors[0]

	# Post processing

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

	def open_pdf(self, root):
		"""
		Open the generated pdf file.
		"""
		pdf_name = root + os.path.extsep + 'pdf'
		self.logger.info('Opening "{0}"...'.format(pdf_name))
		os.system('/usr/bin/open "{0}"'.format(pdf_name))


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
	Typesetter.make_invisible = make_invisible_darwin

class IsolatedTypesetter(Typesetter):

	def __init__(self, **options):
		super(IsolatedTypesetter, self).__init__(**options)
		self.tmp_dir = self.create_tmp_dir()

	tmp_dir_name = '.latex_tmp'

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
				raise IOError('A file named "{0}" already exists in this catalog'.format(tmp_dir))
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

	clean_up = False

	def run(self, tex_path=None):
		# clean up first if needed
		if self.clean_up:
			self.clean_up_tmp_dir()
		super(IsolatedTypesetter, self).run()

	def log_file_path(self, base, file_base):
		return os.path.join(self.tmp_dir, file_base + os.path.extsep + 'log')

	# extensions of the files that will be "pulled back" to the directory where the file is
	# on Mac OS X those files will be set invisible
	move_exts = ['pdfsync', 'aux', 'idx', 'pdf']

	# whereas the pdf file produced will be pulled back in the current directory
	move_pdf_to_curdir = True
	new_pdf_name = ''

	def handle_aux(self, base, file_base):
		"""
		Move some auxiliary files back to the tex directory
		"""
		for aux_ext in self.move_exts:
			aux_name = file_base + os.path.extsep + aux_ext
			src = os.path.join(self.tmp_dir, aux_name)
			dest = os.path.join(base, os.curdir)
			# move the pdf in the current directory
			if aux_ext == 'pdf':
				pdf_name = os.path.join(base, aux_name)
				pdf_path = pdf_name
				if self.move_pdf_to_curdir:
					pdf_path = os.path.join(os.curdir, aux_name)
					pdf_name = aux_name
				if self.new_pdf_name:
					pdf_path = os.path.join(dest, self.new_pdf_name + os.path.extsep + 'pdf')
					pdf_name = dest
				# store the pdf name for later use
				self.current_pdf_name = pdf_name
				# write the pdf data in the existing pdf file
				old_pdf_file = open(pdf_path, 'w')
				try:
					new_pdf_file = open(src, 'r')
				except IOError:
					message = 'pdf file "{0}" not found.'.format(aux_name)
## 					self.logger.error('\n\t%s' % message)
					raise IOError(message)
				contents = new_pdf_file.read()
				old_pdf_file.write(contents)
				old_pdf_file.close()
				new_pdf_file.close()
			else:
				final_path = os.path.join(dest, aux_name)
				try:
					shutil.move(src, final_path)
				except IOError:
					pass

	def arguments(self):
		args = super(IsolatedTypesetter, self).arguments()
		args.append('-output-directory={0}'.format(self.tmp_dir))
		return args
