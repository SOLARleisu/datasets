"""
This module provides handling
of the basic aspects of the patchdata set:
    - building hdf5 stores (for the original sized patches)
      in particular the stores to evaluate descriptors
    - resizing patches (works only on available stores)
    - randomly selecting patches
    - printing general information
"""


import subprocess
import random
from itertools import izip, product
from collections import defaultdict
from os.path import dirname, join, exists
import hashlib
import numpy as np
import h5py

try:
    import Image as img
except:
    import PIL as img


from helpers import helpers


# size of an original patch in pixels
patch_x = 96
patch_y = 96
# color images
channels = 3

# number of classes
classes = 10

# number of training images per class
train_size = 500

# number of test images
test_size = 800

# standard path
_default_path = dirname(__file__) + "./stl10_binary"


def get_store(fname="stl_96x96_train.h5", verbose=True, access='r'):
    if verbose:
        print "Loading from store", fname
    return h5py.File(fname, access)


def build_store(origin="train", path=_default_path):
    """
    """
    if origin is "train":
        fname = "stl_96x96_train.h5"
        size = train_size
        inpts = "train_X.bin"
        lbls = "train_y.bin"
    elif tag is "test":
        fname = "stl_96x96_test.h5"
        size = test_size
        inpts = "test_X.bin"
        lbls = "test_y.bin"
    totals = classes * size
    
    print "Writing to", fname
    h5f = h5py.File(fname, "w")

    # data is available in binary fromat
    f = open(join(path, inpts), "rb")
    
    dset = h5f.create_dataset(name=origin, shape=(totals,\
            channels*patch_x*patch_y), dtype=np.uint8)
    
    for i in xrange(totals):
        for c in xrange(channels):
            uints = f.read(patch_x*patch_y)
            if (len(uints) != patch_x*patch_y):
                print "ERROR: in 'build_store', expected more data."
                print "ERROR: remove the generated file: ", fname
                h5f.close()
                return
            tmp = np.frombuffer(uints, dtype=np.uint8)
            tmp = tmp.reshape(patch_x, patch_y).T
            dset[i, c*patch_x*patch_y:(c+1)*patch_x*patch_y] = tmp.ravel()
    f.close()
    
    f = open(join(path, lbls), "rb")
    cset = h5f.create_dataset(name="trgts",\
            shape=(totals,), dtype=np.int)
    for i in xrange(totals):
        lbl = f.read(1)
        if (len(lbl) != 1):
            print "ERROR: in 'build_store', expected more data."
            print "ERROR: remove the generated file: ", fname
            h5f.close()
            return
        cset[i] = ord(lbl)
    f.close()
 
    h5f.attrs["stl"] = origin 
    h5f.attrs["patch_shape"] = (patch_y, patch_x)
    h5f.attrs["channels"] = channels
    h5f.close()
    print "Wrote store to", fname


def stationary_store(store, eps=1e-8, C=1., div=1., chunk=512, cache=False, exclude=[None], verbose=True):
    """A new store that contains stationary images from _store_.
    """
    if verbose:
        print "Stationarize store", store, "with eps, C, div" , eps, C, div
    sfn = store.filename.split(".")[0]
    name = hashlib.sha1(sfn + str(C) + str(eps) + str(chunk))
    name = name.hexdigest()[:8] + ".stat.h5"
    if cache is True and exists(name):
        print "Using cached version ", name
        return h5py.File(name, 'r+')

    print "No cache, writing to", name
    stat = h5py.File(name, 'w')
    helpers.stationary(store, stat, chunk=chunk, eps=eps, C=C, div=div, exclude=exclude)
    stat.attrs["Stationary"] = "from " + str(store.filename)
    return stat


def resize_store(store, shape, cache=False, exclude=[None], verbose=True):
    """A new store that contains resized images from _store_.
    """
    if verbose:
        print "Resizing store", store, "to new shape", shape
    sfn = store.filename.split(".")[0]
    name = hashlib.sha1(sfn + str(shape))
    name = name.hexdigest()[:8] + ".resz.h5"
    if cache is True and exists(name):
        if verbose: print "Using cached version ", name
        return h5py.File(name, 'r+')

    print "No cache, writing to", name
    rsz = h5py.File(name, 'w')
    helpers.resize(store, rsz, shape, exclude=exclude)
    rsz.attrs["Resized"] = "from " + str(store.filename)
    return rsz


if __name__=="__main__":
    build_store()