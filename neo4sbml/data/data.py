"""
Helper functions to access the data.
"""

import os
data_dir = os.path.dirname(os.path.abspath(__file__))

# /home/mkoenig/neo4sbml/data/BioModels-r29_sbml_curated
example_filepath = os.path.join(data_dir, 'BioModels-r29_sbml_curated', 'BIOMD0000000001.xml')


def get_biomodel_paths():
    """ All paths for the biomodels. """
    dir = os.path.join(data_dir, 'BioModels-r29_sbml_curated')

    # get all SBML files in folder
    files = [os.path.join(dir, f) for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))]
    return sorted(files)


def hash_for_file(filepath, hash_type='MD5', blocksize=65536):
    """ Calculate the md5_hash for a file.

        Calculating a hash for a file is always useful when you need to check if two files
        are identical, or to make sure that the contents of a file were not changed, and to
        check the integrity of a file when it is transmitted over a network.
        he most used algorithms to hash a file are MD5 and SHA-1. They are used because they
        are fast and they provide a good way to identify different files.
        [http://www.pythoncentral.io/hashing-files-with-python/]
    """
    import hashlib

    hasher = None
    if hash_type == 'MD5':
        hasher = hashlib.md5()
    elif hash_type == 'SHA1':
        hasher == hashlib.sha1()
    with open(filepath, 'rb') as f:
        buf = f.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(blocksize)
    return hasher.hexdigest()