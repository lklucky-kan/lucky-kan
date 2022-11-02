#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
from json import dumps


class checkpci(object):

    def __init__(self, keys):
        self.pci_dict = {
            "uesta": {},
            "cesta": {},
        }
        self.keys = keys
        self.logdir = 'reports'
        if not os.path.isdir(self.logdir):
            self.logdir = '.'

    def __call__(self):
        data = self.pcichk()
        if not data:
            return True
        wf = open(os.path.join(self.logdir, 'pci_state.json'), 'w')
        wf.write(dumps(data, indent=4, sort_keys=True))
        wf.close()
        return False

    def get_pci_data(self):
        bus_ls = [e.split()[0].strip() \
                  for e in os.popen('lspci').read().splitlines() if e]
        for e in bus_ls:
            pci_msg = os.popen('lspci -s {0} -vvv 2> /dev/null'.format(e)).read()
            for e1 in pci_msg.splitlines():
                if 'uesta:' in e1.lower() and '+' in e1:
                    self.pci_dict["uesta"][e] = e1.split(':')[1].strip()
                elif 'cesta:' in e1.lower() and '+' in e1:
                    self.pci_dict["cesta"][e] = e1.split(':')[1].strip()
        return self.pci_dict

    def pcichk(self):
        data = self.get_pci_data()
        if not data:
            return True
        err_rd = open(os.path.join(self.logdir, 'errors.log'), 'a')
        for k, v in data.items():
            for k1, v1 in v.items():
                c = 0
                for e in self.keys:
                    if e.lower() in v1.lower():
                        c += 1
                if '+' in v1 and c == 0:
                    err_rd.write('[Lspci]: bus: {0}, {1}: {2}\n'.format(k1, k, v1))
        err_rd.close()
        err_rd = open(os.path.join(self.logdir, 'errors.log'))
        r_data = [e for e in err_rd.read().splitlines() if '[Lspci]' in e]
        err_rd.close()
        if len(r_data) == 0:
            return {}
        return data

if __name__ == '__main__':

    if len(sys.argv) > 1:
        pci_chk = checkpci(keys=sys.argv[1:])
        pci_chk()
