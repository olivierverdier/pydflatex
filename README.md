# ``pydflatex``: a simple build system for LaTeX

## Usage


```sh
pydflatex file.tex
```

Some useful options:

* `-o`: open the pdf in a pdf viewer
* `-k`: keep compiling on error
* `-w`: show the box warnings
* `-l`: only parse existing log

A full list of options is available with `pydflatex --help`.

## Features

``pydflatex`` is a wrapper around ``pdflatex`` which produces a short, readable, coloured output.

The most interesting features are:

- suppressing the logorrhoeic output of LaTeX and giving a coloured, short summary of the warnings and errors instead.
- opening the pdf in your editor of choice

![Screenshot](https://github.com/olivierverdier/pydflatex/raw/master/screenshot.png)


## Compiling Large Documents

``Pydflatex`` is only a shell around the ``pdflatex``, but you can use it along with ``scons`` in order to compile large documents.
In order to do this, create a ``Sconstruct`` file which contains this code:

```python
#!/usr/bin/env python

import os
env = Environment(ENV=os.environ)
env['PDFLATEX'] = 'pydflatex'
env['PDFLATEXFLAGS'] = '-wk'
pdf = env.PDF(target='main.pdf', source='main.tex')
env.Precious(pdf)
```

SCons will now use pydflatex to compile your document.
This will automatically take care of the index, bibliography, recompiling if an included file is modified, etc.

## Using as a Library

It is easy to write a simple python script that calls the typesetter and does precisely what you need in your project.
One way to achieve that would be:

```python
from pydflatex import Typesetter
t = Typesetter(texfilename)
t.typeset_file()
```

## Requirements

- Python v.2.6 (because of the new string formatting)
- ``termstyle`` (optional but strongly advised): to display results in colour
