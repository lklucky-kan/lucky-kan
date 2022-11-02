#!/usr/bin/python
# -*- coding: utf-8 -*-

from sys import argv
from re import search
from json import dumps
from os import listdir, stat
from os.path import join, isdir
from time import mktime, strptime, strftime, localtime


class checksys(object):

    def __init__(self, keys):
        self.key_ls = keys
        self.regex = r'^\w{3}\s{1,2}\d{1,2}\s(\d{2}\:){2}\d{2}\s'
        self.logdir = 'reports'
        if not isdir(self.logdir):
            self.logdir = '.'

    def __call__(self):
        data = self.getMocLog()
        if not data:
            return True
        wf = open(join(self.logdir, 'filter_messages.json'), 'w')
        wf.write(dumps(data, indent=4, sort_keys=True))
        wf.close()
        return False

    def dateTotimestamp(self, date, y):
        st = ' '.join([date.split()[0],
                       date.split()[1].zfill(2),
                       date.split()[2],
                       y])
        ts = int(mktime(strptime(st, "%b %d %H:%M:%S %Y")))
        return st, ts

    def parseMocLog(self, keys):
        tmp = []
        data = {}
        for e in listdir('/var/log'):
            file = join('/var/log', e)
            year = strftime("%Y", localtime(int(stat(file).st_atime)))
            if 'messages' in e:
                rf = open(file)
                tmp = tmp + rf.read().splitlines()
                rf.close()
        tmp = [e for e in tmp \
               if search(self.regex, e)]
        start_date, start_timestamp = self.dateTotimestamp(date=tmp[0], y=year)
        for i, e in enumerate(tmp):
            idx = str(i)
            for e1 in keys:
                if e1.lower() in e.lower():
                    data[idx] = {}
                    strtime, timestamp = self.dateTotimestamp(date=e, y=year)
                    time_mark = (timestamp - start_timestamp) / 60 / 60
                    data[idx]["msg"] = e
                    data[idx]["str_time"] = strtime
                    data[idx]["timestamp"] = timestamp
                    data[idx]["time_mark"] = str(time_mark).zfill(2)
                    break
        return data

    def getMocLog(self):
        data = self.parseMocLog(keys=self.key_ls)
        if not data:
            return {}
        log_data = {}
        for k, v in data.items():
            if v["time_mark"] not in log_data:
                log_data[v["time_mark"]] = []
            log_data[v["time_mark"]].append(v["msg"])
        af = open(join(self.logdir, 'moc_messages.log'), 'w')
        af.write('############################################################\n')
        af.write('## WARNING: Occur count little equals than 5 (count <= 5) ##\n')
        af.write('## ERROR:   Occur count large than 5 (count > 5)          ##\n')
        af.write('############################################################\n\n')
        af.write('| LEVEL |   KEY NAME  |  OCCUR TIME  |  OCCUR COUNT  |' +
                 '         REMARKS        |\n')
        for k, v in sorted(log_data.items()):
            if len(v) <= 5:
                msg = 'WARNING: key: {0}, at {1}th hour, occur count: {2}'. \
                       format(str(self.key_ls),
                              str(int(k)).rjust(2, ' '),
                              len(v))
                af.write(msg + '\n')
            elif len(v) > 5:
                msg1 = 'ERROR: key: {0}, at {1}th hour, occur count: {2},'. \
                       format(str(self.key_ls),
                              str(int(k)).rjust(2, ' '),
                              len(v)) + \
                       ' as following messages:'
                msg2 = ',\n'.join([(' ' * 4) + ' --> ' + e for e in v])
                af.write(msg1 + '\n')
                af.write(msg2 + '\n\n')
        af.close()
        return log_data

if __name__ == '__main__':

    if len(argv) > 1:
        message = checksys(sys.argv[1:])
        message()

