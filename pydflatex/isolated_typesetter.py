#!/usr/bin/env python
# coding: UTF-8
from __future__ import division

"""
Obsolete.
"""
import shutil

class IsolatedTypesetter(Processor):

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
