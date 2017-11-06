#!/usr/bin/python3
from glob import glob
from subprocess import call
import os

from PyQt5.uic import compileUi


HERE = os.path.abspath(os.path.dirname(__file__))


def ui():
    for uifile in glob(os.path.join(HERE, "app/ui/*.ui")):
        pyfile = os.path.splitext(uifile)[0] + ".py"
        print(uifile)
        pyfile = open(pyfile, "wt", encoding="utf-8")
        uifile = open(uifile, "rt", encoding="utf-8")
        compileUi(uifile, pyfile, from_imports=True)


def resource():
    for resfile in glob(os.path.join(HERE, "app/ui/*.qrc")):
        pyfile = os.path.splitext(resfile)[0] + "_rc.py"
        print(resfile)
        call("pyrcc5 -o {} {}".format(pyfile, resfile), shell=True)


if __name__ == "__main__":
    ui()
    resource()
