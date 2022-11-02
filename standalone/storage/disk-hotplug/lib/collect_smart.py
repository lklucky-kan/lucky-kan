#!/usr/bin/python
# -*- coding: utf-8 -*-

from sys import argv
from time import sleep
from stat import S_ISBLK
from shutil import rmtree
from json import load, dump, dumps
from os import stat, popen, system, remove, mkdir, makedirs
from os.path import isfile, isdir, exists, join, basename, abspath

split_line = '\n%s\n' % ('=' * 80)

def get_osdisk():
    get_os_cmd1 = "df | grep -i /boot | awk '{print $1}' | " +\
                  "grep -Eo '/dev/sd[a-z]+' | head -n1"
    get_os_cmd2 = "df | awk '{print $1 \":\" $6}' | grep /$ | " + \
                  "grep -Eo '/dev/sd[a-z]+'"
    dev = popen(get_os_cmd1).read().replace('\n', '').strip()
    if not dev or not exists(dev):
        dev = popen(get_os_cmd2).read().replace('\n', '').strip()
    if not exists(dev):
        return '/dev/sda'
    return dev

os_drive = get_osdisk()
os_letter = basename(os_drive)

def fopen(file='', content='',
          mode='r', json=False):
    data = ''
    f = open(file, mode)
    if mode == 'w' or mode == 'a':
        if json:
            f.write(dumps(content, indent=4, sort_keys=False) + '\n')
        else:
            f.write(str(content))
    else:
        if json:
            data = eval(f.read())
        else:
            data = f.read()
    f.close()
    return data

def sd_list_get(sys_drive=False):
    if sys_drive:
        cmd = "grep -P 'sd\w+$' /proc/partitions | grep -Pv '\d+$' | " + \
              "grep -vE usb | awk '{print $NF}' 2> /dev/null"
    else:
        cmd = "grep -P 'sd\w+$' /proc/partitions | grep -Pv '\d+$' | " + \
              "grep -vE \"usb|%s\" | awk '{print $NF}'" % os_letter + \
              " 2> /dev/null"
    drive_ls = popen(cmd).read().splitlines()
    drive_ls = ['/dev/' + e for e in drive_ls]
    return drive_ls

def nvme_list_get(sys_drive=False):
    nvme_ls = []
    cmd = "grep -P 'nvme\w+$' /proc/partitions | grep -Pv 'p\d+$' | " + \
          "awk '{print $NF}' 2> /dev/null"
    nvme_info = popen(cmd).read().splitlines()
    nvme_ls = ['/dev/' + e for e in nvme_info if os_letter + ' ' not in e]
    if sys_drive and '/dev/nvme' in os_drive:
        nvme_ls.insert(0, os_drive)
    return nvme_ls

def collect_smart(operation):
    logdir = 'reports/smart'
    if operation == 'before':
        if isdir(logdir):
            rmtree(logdir)
        makedirs(logdir, 0o755)
    drive_dict = {
        "drive_ls": sd_list_get(sys_drive=True),
        "nvme_ls": nvme_list_get(sys_drive=True),
    }
    for e in drive_dict["drive_ls"]:
        log = popen('smartctl -a ' + e + ' 2> /dev/null').read()
        fopen(file=join(logdir, 'smart_sata_{0}.log'.format(operation)),
              content='### below is disk %s smart log ###\n' %e + log,
              mode='a')
        fopen(file=join(logdir, 'smart_sata_{0}.log'.format(operation)),
              content=split_line,
              mode='a')
    for e1 in drive_dict['nvme_ls']:
        for e2 in ['smart-log', 'id-ctrl', 'error-log']:
            log = popen('{0} {1} {2} 2> /dev/null'. \
                        format(e, e2, e1)).read()
            logname = join(logdir, '{0}_{1}_{2}.log'. \
                           format(e, e2.replace('-', '_'), operation))
            fopen(file=logname,
                  content='Drive - {0}\n'.format(e1),
                  mode='a')
            fopen(file=logname, content=log, mode='a')
            fopen(file=logname, content=split_line, mode='a')

if __name__ == '__main__':
    collect_smart(argv[1])
