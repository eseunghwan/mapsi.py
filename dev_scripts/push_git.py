# -*- coding: utf-8 -*-
import os

__dir__ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(__dir__)
os.system("git push -u origin master --force")
