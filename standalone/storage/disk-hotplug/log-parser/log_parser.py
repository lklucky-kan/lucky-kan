#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os, re
c_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(c_path)
from sys import argv
from time import sleep
from shutil import copy, rmtree
from re import search, sub
from platform import platform
from os import popen, mkdir, chmod, listdir, remove, system
from os.path import join, isfile, isdir, basename, splitext
from argparse import ArgumentParser, RawTextHelpFormatter

tea_path = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.pardir,
        os.pardir,
        os.pardir
        )
)
sys.path.insert(0, tea_path)
from datetime import datetime
import logging, os, shutil
from pprint import pprint

# Import own modules
sys.path.append('./lib')
from pci_chk import checkpci
from sys_chk import checksys


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

class Logger():
    '''
    logging module for TEA. Encapsulated python logging module.
    author: yuhanhou
    '''

    def __init__(self, **kwargs):
        self.log_file = kwargs.get('log_file')
        self.stdoutput = kwargs.get('stdoutput', True)
        self.log_file_timestamp = kwargs.get('log_file_timestamp', True)
        self.log_level = kwargs.get('log_level', 'DEBUG').upper()
        self.log_formatter = kwargs.get('log_formatter', '%(asctime)s %(levelname)s: %(message)s')

        if self.log_file and 'name' not in kwargs:
            self.name = self.log_file #logger's name
        else:
            self.name = kwargs.get('name', 'TEA')

        self.logger = logging.getLogger(self.name)

        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        # formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s') 
        formatter = logging.Formatter(self.log_formatter) 

        LEVEL = {
                    "ERROR" : logging.ERROR,
                    "WARNING" : logging.WARNING,
                    "INFO" : logging.INFO,
                    "DEBUG" : logging.DEBUG,
                    "CRITICAL" : logging.CRITICAL,
                } 
        
        self.logger.setLevel(LEVEL[self.log_level])

        #set console output:
        console_output = False

        #check if screen output is set:
        for hd in self.logger.handlers:
            if not isinstance(hd, logging.FileHandler) and isinstance(hd, logging.StreamHandler):
                console_output = True
                break

        if self.stdoutput and not console_output:
            console = logging.StreamHandler()
            console.setLevel(LEVEL[self.log_level])
            console.setFormatter(formatter)
            self.logger.addHandler(console)
    
        #set log file:
        if self.log_file:  
            if self.log_file_timestamp:
                self.log_file = self.log_file + '_' + timestamp + ".log"

            fh = logging.FileHandler(self.log_file)                
            fh.setLevel(LEVEL[self.log_level])
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
    
    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)
        
    def info(self, msg, *args, **kwargs):        
        self.logger.info(msg, *args, **kwargs)  
    
    def warn(self, msg, *args, **kwargs):        
        self.logger.warning(msg, *args, **kwargs) 
            
    def error(self, msg, *args, **kwargs):        
        self.logger.error(msg, *args, **kwargs)   
        
    def critical(self, msg, *args, **kwargs):        
        self.logger.critical(msg, *args, **kwargs) 


class LogParser(object):

    def __init__(self):
        self.status = 'ERROR'
        self.regex = r'^\[(Lspci|Moclog|Sellog|Sdrlog|Dmesg|Messages)\]\:\s'
        if not isdir('reports'):
            mkdir('reports')

    def clean_syslog(self, blact_white_dict):
        logger.info('Clear system log before test begin...')
        for k, v in blact_white_dict.items():
            if k in ['pci']:
                continue
            logger.info(
                'Starting clear %s logs by running cmd:\n' %k +
                '    %s' %v['clear_cmd']
            )
            log = popen(v['clear_cmd']).read()
            logger.info('Result:\n%s' %log)
            # clear messages while it empty
            if k == 'messages':
                msg_log = fopen(file='/var/log/messages'). \
                                       replace('\n', '')
                while search(r'\d+|\w+', msg_log):
                    log = popen(v['clear_cmd']).read()

    def collect_syslog(self, logs):
        for k, v in logs.items():
            if 'ipmi_cmd' in v:
                for e in v['ipmi_cmd']:
                    name = e.split(':')[0].strip()
                    cmd = e.split(':')[1].strip()
                    log = popen(cmd).read()
                    fopen(
                        file='reports/{0}.log'.format(name),
                        content=log,
                        mode='w'
                    )
            else:
                log = popen(v['cmd']).read()
                fopen(
                    file='reports/{0}.log'.format(k),
                    content=log,
                    mode='w'
                )

    def sdr_check(self):
        sdr_logs = fopen(file='reports/sdr.log').splitlines()
        sdr_logs = [ e.strip() for e in sdr_logs if e.strip() ]
        err_list = []
        for e in sdr_logs:
            status = e.split('|')[2].strip().lower()
            if status in ['ok', 'ns']:
                continue
            else:
                err_list.append(e)
        if len(err_list) > 0:
            logger.info('SDR log check FAIL')
            fopen(
                file='reports/errors.log',
                content='### Below is SDR error log ###\n' + '\n'.join(err_list),
                mode='a'
            )
        else:
            logger.info('SDR log check PASS')

    def check_log(self, logfile, logtype):
        err_list = []
        log_list = fopen(file=logfile).splitlines()
        log_list = [ l for l in log_list if l.strip() ]
        for l in log_list:
            for err in bw_dict[logtype]['black_list']:
                if re.search(err, l, re.I):
                    err_list.append(l)
                    break
            for wt in bw_dict[logtype]['white_list']:
                if re.search(wt, l, re.I) and l in err_list:
                    err_list.remove(l)
                    break
        if len(err_list) > 0:
            logger.info('%s log check FAIL' %(os.path.basename(logfile).split('.')[0]))
            fopen(
                file='reports/errors.log',
                content='### Below is %s error log ###\n' %os.path.basename(logfile).split('.')[0] + '\n'.join(err_list),
                mode='a'
            )
        else:
            logger.info('%s log check PASS' %(os.path.basename(logfile).split('.')[0]))

    def pci_check(self):
        pci_info = checkpci(keys=bw_dict["pci"]["white_list"])
        if pci_info():
            logger.info('Lspci info check PASS')
        else:
            logger.info('Lspci info check FAIL')

    def cleanlog(self, logpath='reports/'):
        rmtree(logpath)
        self.__init__()

    def logparse(self):
        # check all logs are exist
        logger.info('\nStarting check log in reports folder' + \
              ' log...\n')
        if isfile('reports/errors.log'):
            remove('reports/errors.log')
            self.__init__()

        lnm_list = [ os.path.basename(l) for l in logname_list ]
        for log in os.listdir('reports'):
            if log not in lnm_list and log != 'errors.log':
                print('log "%s" in reports will not parser, please modify it as format "%s"' %(log, lnm_list))
            elif log == 'sel.log':
                self.check_log('reports/sel.log', 'bmc')
            elif log == 'dmesg.log':
                self.check_log('reports/dmesg.log', 'dmesg')
            elif log == 'messages.log':
                self.check_log('reports/messages.log', 'messages')
            elif log == 'sdr.log':
                self.sdr_check()
            elif log == 'pci.log':
                self.pci_check()

if __name__ == '__main__':

    # define global variables
    logname_list = [
        'reports/sel.log',
        'reports/sel_vlist.log',
        'reports/sdr.log',
        'reports/pci.log',
        'reports/dmesg.log',
        'reports/messages.log'
    ]

    if len(argv) == 1:
        print("Try '-h/--help' for test user guide.")
        raise SystemExit(-1)

    # parse arguments
    parser = ArgumentParser(
        description='Parser Logs',
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument('-a', '--after',
                      action='store_true',
                      help='collect and check system log after normal test finished')
    parser.add_argument('-b', '--before',
                      action='store_true',
                      help='clear system log before normal test begin')
    parser.add_argument('-op', '--onlyparse',
                      action='store_true',
                      help='only parse logs in forder "reports"')
    parser.add_argument('-oc', '--onlycollect',
                      action='store_true',
                      help='only collect system log and not check it')

    args = parser.parse_args()
    before = args.before
    after = args.after
    only_par = args.onlyparse
    only_collect = args.onlycollect

    logger = Logger(log_file='Result')

    # start test
    chktest = LogParser()

    blk_white_file=os.path.join(c_path, 'data', 'black_white.json')

    # read the black white list table
    with open(blk_white_file) as jrf:
        bw_dict = eval(jrf.read())

    # check args
    if before + after + only_par + only_collect != 1:
        print("argument [-b/-a/-op/oc] can only choose one")
        raise SystemExit(-1)

    # parser log in reports only
    if only_par:
        ret = chktest.logparse()
        raise SystemExit(ret)

    # check ipmitool
    ipmi_log = popen('command -v ipmitool').read().replace('\n', '')
    ipmi_stout = popen('ipmitool 2>&1').read().replace('\n', '')
    if not ipmi_log:
        print("Please install tool 'ipmitool' first")
        raise SystemExit(-1)
    elif 'Could not open device' in ipmi_stout:
        print(ipmi_stout)
        raise SystemExit(-1)

    # chean reports path
    chktest.cleanlog()

    # clear sel/dmesg/message log
    if before:
        chktest.clean_syslog(bw_dict)
    # only collect system logs
    elif only_collect:
        chktest.collect_syslog(bw_dict)
    # only parser logs in reports dir
    elif only_par:
        chktest.logparse()
    # collect and check all system logs
    elif after:
        chktest.collect_syslog(bw_dict)
        chktest.logparse()
