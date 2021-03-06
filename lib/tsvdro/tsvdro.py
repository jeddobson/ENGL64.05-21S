#
# tsvdro: reference implementation for data rich tab separated value objects
#         reads and writes DRO objects stored as JSON data
#
# Jed Dobson (james.e.dobson@dartmouth.edu)
# Dartmouth College
# http://www.dartmouth.edu/~jed
#
#
# implements tsvdro_ver 1.0
#

import numpy as np
import platform
import sys, os
import time
import json

__version__ = '1.0.1'

# build the basic header
def build_header():
   ''' Build the basic DRO object header '''

   header = dict()

   # version number is a string (not version of module, but the format version)
   header['tsvdro_ver']  = "1.0"

   # build workflow section
   header['workflow'] = dict()
   header['workflow']['created_date'] = time.strftime("%Y-%m-%d %H:%M")
   header['workflow']['last_updated'] = time.strftime("%Y-%m-%d %H:%M")
   header['workflow']['created_by'] = "tsvdro_reference_implementation"
   header['workflow']['created_system'] = platform.node()

   # data_type: allow different types and formats of data to be stored
   # 1: TSV 
   # 2: Segmented TSV
   header['workflow']['data_type'] = 1
   header['workflow']['data_option'] = None

   # include total count of tokens in documents (store prior to preprocessing)
   # and unique tokens (vocab_count)
   header['workflow']['vocab_count'] = None
   header['workflow']['token_count'] = None

   # build bibliographic section
   header['bibliographic_data'] = dict()
   header['bibliographic_data']['author_name'] = None
   header['bibliographic_data']['title'] = None
   header['bibliographic_data']['volumes'] = None
   header['bibliographic_data']['pages'] = None
   header['bibliographic_data']['publication_date'] = None
   header['bibliographic_data']['publisher'] = None
   header['bibliographic_data']['publisher_location'] = None
   header['bibliographic_data']['file_uri'] = None

   return(header)


# function to load a file
def load(filename):
   ''' Load DRO file with the supplied filename
   Returns TSVDRO object
   '''

   try:
      f = open(filename)
   except NameError:
      print('Missing filename')
      return
   except FileNotFoundError:
      print('Cannot locate file:',filename)
      return

   # default format is JSONified data rich object
   # try to read JSON data

   try:
       file_object = json.load(f)

   #
   # If read fails, try to read as plain text
   # 
 
   except json.decoder.JSONDecodeError:

       # assume TSV file
       import csv

       # we will need to construct some data
       print('Not in DRO format: converting')

       tsvdro_object = dict()

       tsv_data = dict()
       with open(filename) as input:

           input = csv.reader(input, delimiter='\t',quoting=csv.QUOTE_NONE)
           for row in input:

              # add data as dict
              # and only if we have two colums of data
              if len(row) == 2:

                  # only if we can convert to integer
                  if row[1].isdigit():
                      tsv_data[row[0]] = int(row[1])

       tsvdro_object['data'] = tsv_data

       # construct a header
       header = build_header()
       tsvdro_object['header'] = header

       return(tsvdro_object)

   # read the JSON object and return
   tsvdro_object = file_object

   # verify object
   if verify(tsvdro_object) == False:
      print("ERROR: Data potentially corrupted")
   return(tsvdro_object)


#
# function to verify that we actually have a DRO object
# 

def verify(dro_object):
   ''' Verify the integrity of the DRO object '''

   # what is the object?
   if type(dro_object) == dict:
      try:
        len(dro_object['header']['tsvdro_ver'])
        return True
      except KeyError:
        return False
   else:
       return False

def save(dro_object,filename):
   ''' Saves DRO object with the supplied filename
   '''
   # first verify that this is a good DRO object
   if verify(dro_object):
     # modify with 'last_updated' timestamp
     dro_object['header']['workflow']['last_updated'] = time.strftime("%Y-%m-%d %H:%M")
     with open(filename, "w") as f:
        json.dump(dro_object, f)
     return

   else:
    print("ERROR: invalid DRO object")

def cv2dro(vectorized_object,vectorizer):
    ''' The cv2dro turns the output of CountVectorize text into a DRO object
    '''

    # make sure CountVectorizer is available
    from sklearn.feature_extraction.text import CountVectorizer

    if vectorized_object.ndim > 2:
        print("only a single dimension (single text or document) object supported")
        return
    
    # obtain vocabulary
    vocab = vectorizer.get_feature_names()
    
    # order by the object's index (the vocabulary)
    vectorized_object.sort_indices()
    
    # create a header
    tsvdro_object = dict()
    tsvdro_object['header'] = build_header()
    
    # explain where we found this object
    tsvdro_object['header']['workflow']['created_by'] = "cv2dro"

    # we do have this information
    tsvdro_object['header']['workflow']['vocab_count'] = len(vocab)
    
    # create data section
    tsvdro_object['data'] = dict()
    
    for i, value in enumerate(vectorized_object.toarray()[0]):
        # entry in table indicates single appearance, so add '1' to value
        value+= 1 

        token = vocab[i]
        tsvdro_object['data'][token] = value
    
    return tsvdro_object

