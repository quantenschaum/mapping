#!/usr/bin/env python3
# coding: utf-8

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
try:
  from rich_argparse import ArgumentDefaultsRichHelpFormatter as ArgumentDefaultsHelpFormatter
except: pass

import os
import re
from subprocess import run

TEX=r'''\documentclass{article}
% Support for PDF inclusion
% https://leolca.blogspot.com/2010/06/pdfposter.html
\usepackage[final]{pdfpages}
% Support for PDF scaling
\usepackage{graphicx}
\usepackage[dvips=false,pdftex=false,vtex=false]{geometry}
\geometry{paperwidth=190mm, paperheight=277mm}
\usepackage[cam,a4,center,pdflatex]{crop}
\begin{document}
% Globals: include all pages, don't auto scale
\includepdf[pages=-,pagecommand={\thispagestyle{plain}}]{pages.pdf}
\end{document}
'''

def main():
  parser = ArgumentParser(description="poster printer based on pdfposter and LaTeX",formatter_class=ArgumentDefaultsHelpFormatter)
  parser.add_argument("input", help="input PDF")
  parser.add_argument("output", help="output PDF", nargs='?')
  parser.add_argument("-s",'--scale', help="scale factor")
  parser.add_argument("-p",'--pages', help="output pages",default='2x2')
  parser.add_argument("-m",'--media', help="media size, printable area",default='190x277mm')
  args = parser.parse_args()

  output=args.output or args.input.replace('.pdf','.sheets.pdf')

  if args.scale:
    opts=f'-s{args.scale}'
  else:
    m=re.match(r'(\d+)x(\d+)(.+)',args.media)
    x,y,u=int(m.group(1)),int(m.group(2)),m.group(3)
    n,m=list(map(int,args.pages.split('x')))
    opts=f'-p{n*x-1}x{m*y-1}{u}'

  run(f'pdfposter -m{args.media} {opts} "{args.input}" pages.pdf',shell=True,check=True)

  with open('sheets.tex','w') as f: f.write(TEX)
  run(f'latexmk -pdf -interaction=nonstopmode sheets.tex',shell=True,check=True)
  os.rename('sheets.pdf',output)
  os.remove('pages.pdf')
  run(f'latexmk -C',shell=True,check=True)


if __name__=='__main__': main()
