# `pydflatex`: a simple LaTeX wrapper

``pydflatex`` is a wrapper around ``pdflatex`` which produces a short, readable, coloured output.
Specifically, `pydflatex` 

- runs `pdflatex`/`xelatex` blazingly fast using the -batchmode option
- prints out a coloured, short summary of the warnings and errors
- hides the temporary files in various ways
- opens the pdf file if needed

![Screenshot](https://github.com/olivierverdier/pydflatex/raw/master/screenshot.png)

## Usage


```sh
pydflatex file.tex
```

Some useful options:

* `-x`: run `xelatex` instead of `pdflatex`
* `-k`: keep compiling on error
* `-o`: open the pdf in a pdf viewer
* `-l`: only parse existing log

A full list of options is available by running `pydflatex --help`.

## Install

You can install pydflatex by running

```sh
pip install -e "git+https://github.com/olivierverdier/pydflatex#egg=pydflatex"
pip install blessings
```


## Using as a Library

`pydflatex` is a collection of several independent modules to typeset the file, analyze its log, hiding the auxilliary files, etc.
It is easy to write a simple python script that calls either one of those modules and does exactly what you want in your project.

For instance, to run a given file with `xelatex` you can call:

```python
from pydflatex import Typesetter
t = Typesetter(options={'xetex'=True})
t.typeset(path_to_file)
```

In order to just print the summary of the log:
```python
from pydflatex import LogProcessor
l = LogProcessor()
l.process_log(path_to_log_file)
```

Feel free to check out the other modules inside the `pydflatex` folder.

## Requirements

- [`blessings`](https://github.com/erikrose/blessings) (optional but strongly advised): to display results in colour
