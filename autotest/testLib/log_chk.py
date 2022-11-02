#!/usr/bin/python3

import os, sys
from os import popen, system
tea_path = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.pardir,
        os.pardir
        )
)
sys.path.append(tea_path)
from common.other.log import Logger

class Logchk():
    def __init__(self, **kwargs):
        '''
        description: Check various of system log
        author: Kail
        params: logger, the logfile
        '''
        self.logger = kwargs.get('logger')

    def chk_dmesg(self):
        '''
        description: check dmesg log
        author: Kail
        params: None
        return: dmesg_error, The error dmesg info
        '''
        dmesg_error = popen("dmesg|grep -iE 'error|fail|warn|wrong|bug|respond|pending'").read().strip()
        return dmesg_error
