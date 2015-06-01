"""

@author: mkoenig
@date: 2015-06-01
"""

from __future__ import print_function
import libsbml
import os


class Class1(object):
    def __init__(self, path):
        self.doc = libsbml.readSBMLFromFile(path)
        self.model = self.doc.getModel()

class Class2(object):
    def __init__(self, path):
        doc = libsbml.readSBMLFromFile(path)
        self.model = doc.getModel()

if __name__ == "__main__":
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'BIOMD0000000001.xml')

    # no problem
    t1 = Class1(path)
    print(t1.model)

    # doc is garbage collected and model not available any more, despite reference to model
    t2 = Class2(path)
    print(t2.model)
