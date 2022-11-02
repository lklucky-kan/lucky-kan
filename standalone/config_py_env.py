#!/usr/bin/python3
'''
description:this script is to install the python modules and set PYTHONPATH env vars.
            assume the python3 is installed on the server and tea/requirements.txt 
            exists with python module listed. It can be called in each standalone 
            scripts located in tea/standalone.
author: yuhanhou
params: NA
'''
import os
import re
import sys
sys.path.insert(0, '..')
from common.communication.local import Local
from common.other.log import Logger

#get current tea path
cur_path = os.getcwd()
current_tea_path = ''
match = re.search(r'^(\S+tea)', cur_path)
if match:
    current_tea_path = match.group(1)

#install python third party modules, network connection is needed.
logger = Logger(log_file='pyconfig.log', stdoutput=False)
local_os = Local(logger=logger)
path_sep = '/'

try:
    try_out = local_os.cmd('ls') #try if ls is successfully run, if yes, this is linux and path seprator is /
except Exception as e: #encoding error will occurred if on windows
    path_sep = '\\'

print('try to install required python modules...')
local_os.cmd('pip3 install -U pip')
local_os.cmd('pip3 install -r ' + current_tea_path + path_sep +  'requirements.txt')

