``pydflatex``: a simple build system for LaTeX
================================================

What pydflatex does
*******************

``pydflatex`` is another tool to help compiling LaTeX files.

The most interesting features are:

- running LaTeX as many times as necessary
- hiding the auxilliary files in a sub-folder (defaults to ``.tmp_latex``)
- suppressing the logorrheic output of LaTeX and giving a coloured, short summary of the warnings and errors instead.
- some extra features on Mac OS X, as opening the pdf in you editor of choice, or hiding the remaining auxilliary files (``.pdfsync`` files)

What pydflatex does not
***********************

It will not run ``bibtex`` or ``makeidx`` for you, but it is easy enough to write a simple python script that calls the typesetter and does precisely what you need in your project. One way to achieve that would be::

	from pydflatex import Typesetter
	t = Typesetter()
	t.typeset_file(texfilename)
