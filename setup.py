#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from distutils.core import setup

setup(
	name = 'pydflatex',
	description = 'LaTeX wrapper',
	author='Olivier Verdier',
	license = 'GPL',
	keywords = ['LaTeX', 'pdflatex', 'parser'],
	
	scripts=['bin/pydflatex'],
	packages=['pydflatex'],
	classifiers = [
	'Development Status :: 5 - Production/Stable',
	'Environment :: Console',
	'Intended Audience :: Science/Research',
	'License :: OSI Approved :: GNU General Public License (GPL)',
	'Operating System :: OS Independent',
	'Programming Language :: Python',
	'Topic :: Text Processing :: Markup :: LaTeX'],
	zip_safe = False,
	)
