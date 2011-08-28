``pydflatex``: a simple build system for LaTeX
================================================

Usage
*******

::

    pydflatex file.tex

Some useful options:

 :`-p`: opens the pdf in a pdf viewer
 :`-k`: keeps compiling on error
 :`-w`: suppress the box warnings

Features
*******************

``pydflatex`` is a wrapper around ``pdflatex`` which produces a short, readable, coloured output.

The most interesting features are:

- suppressing the logorrhoeic output of LaTeX and giving a coloured, short summary of the warnings and errors instead.
- opening the pdf in you editor of choice

.. image:: http://files.droplr.com/files/35740123/Lp66.pydflatex.png
	:alt: Example


Limitations
***********************

It will not run ``bibtex`` or ``makeidx`` for you, but it is easy enough to write a simple python script that calls the typesetter and does precisely what you need in your project. One way to achieve that would be::

	from pydflatex import Typesetter
	t = Typesetter()
	t.typeset_file(texfilename)

Requirements
************

- Python v.2.6 (because of the new string formatting)
- ``termstyle`` (optional but strongly advised): to display results in colour
