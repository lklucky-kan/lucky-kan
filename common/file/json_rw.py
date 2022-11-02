#!/bin/bash

from json import dumps
import shutil, os
import tarfile

def fopen(file='', content='', mode='r', json=False):
    '''
    description: read or write file
    author: Kail
    params: file, the file want to operate.
            content, the msg that want to be written to file.
            mode, the open file mode, choose from [r, w, a]
            json, use when deal json date, choices:[True, False]
    return: data, the file's reading date
    '''
    # transfer dat file to dat_dict
    data = ''
    f = open(file, mode, encoding='UTF-8')
    if mode == 'w' or mode == 'a':
        if json:
            f.write(dumps(content, indent=4, sort_keys=False) + '\n')
        else:
            f.write(content + "\n")
    else:
        if json:
            data = eval(f.read())
        else:
            data = f.read()
    f.close()
    return data


def clean_paths(*paths):
    '''
    description: create a new floder or clean folder/folderlist
    author: Kail
    params: *paths, a path tuple
    return: Null
    '''
    for path in paths:
        if type(path) is list or type(path) is tuple:
            for p in path:
                if os.path.exists(p):
                    shutil.rmtree(p)
                os.makedirs(p)
        else:
            #print(path, type(path))
            if os.path.exists(path):
                shutil.rmtree(path)
            os.makedirs(path)

def init_paths(*paths):
    '''
    description: create the folder if folder not exist
    author: Kail
    params: *paths, a path tuple
    return: Null
    '''
    for path in paths:
        if type(path) is list or type(path) is tuple:
            [ os.makedirs(p) for p in path if not os.path.exists(p) ]
        else:
            #print(path, type(path))
            if not os.path.exists(path): os.makedirs(path)

class Pack():
    def __init__(self):
        pass

    @classmethod
    def pack_targz(self, output_file, source_dir):
        '''
        description: package dir 'source_dir' to tar.gz file 'output_file'
        author: Kail
        params: output_file, the output tar.gz file name, type str.
                source_dir, the dir which want to package, type str.
        return: None
        '''
        with tarfile.open(output_file, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))
