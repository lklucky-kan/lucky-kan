import os
import platform
import re
import csv
import pandas as pd


def massge_csv(csv_name, name, fr):
    if not os.path.exists(csv_name):
        create_csvlog(csv_name, name)
    info_list = get_csv_info(name, fr)
    print(info_list)
    write_csvlog(csv_name, info_list)


def get_csv_info(name, fr):
    info_list = []
    reader = csv.reader(fr)
    colum = next(reader)
    print(colum)
    while True:
        try:
            colum1 = next(reader)
            colum2 = colum1.insert(0, name)
            print(colum2)
            info_list.append(colum1)
        except StopIteration:
            break
    return info_list


def get_csv_list(path):
    csv_list = []
    for pkg, subdirectory, file in os.walk(path):
        if platform.system() == 'Windows':
            a = re.sub('\\\\', '.', pkg)
        elif platform.system() == "Linux":
            a = re.sub('/', '.', pkg)
        else:
            a = None
        if file:
            for file_info in file:
                pyfile = re.findall('.*data\.csv$', file_info)
                if pyfile:
                    name = pyfile[0].split('_')[0]
                    path = f'{name}/{pyfile[0]}'
                    print(path)
                    with open(path, 'r') as fr:
                        if 'random_write' in path:
                            csv_name = 'random_write.csv'
                            massge_csv(csv_name, name, fr)
                        elif 'random_read' in path:
                            csv_name = 'random_read.csv'
                            massge_csv(csv_name, name, fr)
                        elif 'seq_read' in path:
                            csv_name = 'seq_read.csv'
                            massge_csv(csv_name, name, fr)
                        elif 'seq_write' in path:
                            csv_name = 'seq_write.csv'
                            massge_csv(csv_name, name, fr)
                        elif 'mix' in path:
                            csv_name = 'mix.csv'
                            if not os.path.exists(csv_name):
                                create_csvlog(csv_name, 'mix')
                            massge_csv(csv_name, name, fr)

    return csv_list


def create_csvlog(csv_log, mode):
    if mode == 'mix':
        data = [
            ['', 'Block size', ' IO type', ' Jobs', ' Queue Depth', ' WR/RD', ' IOPS', ' Lantency(us)', ' Qos(us) 99%',
             ' Qos(us) 99_9%', ' Qos(us) 99_99%', ' WR/RD', ' IOPS', ' Lantency(us)', ' Qos(us) 99%',
             ' Qos(us) 99_9%', ' Qos(us) 99_99%'], ]
    else:
        data = [['', 'Block size', ' IO type', ' WR/RD', ' Jobs', ' Queue Depth', ' Bandwidth(kB/s)', ' Lantency(us)',
                 ' Qos(us) 99%', ' Qos(us) 99_9%', ' Qos(us) 99_99%']]
    with open(csv_log, 'w') as fw:
        writer = csv.writer(fw)
        for row in data:
            writer.writerow(row)


def write_csvlog(csv_name, data):
    with open(csv_name, 'a') as fw:
        writer = csv.writer(fw)
        for row in [data]:
            writer.writerows(row)


def csv_excel(csv_name, sheetname):
    if os.path.exists(csv_name):
        data1 = pd.read_csv(csv_name, encoding="gbk", index_col=0)
        data1.to_excel(writer, sheet_name=sheetname)
        writer.save()


csv_list = get_csv_list('./')

writer = pd.ExcelWriter('clearup_csvlog.xlsx')
csv_excel("random_read.csv", 'random_read')
csv_excel("random_write.csv", 'random_write')
csv_excel("seq_read.csv", 'seq_read')
csv_excel("seq_write.csv", 'seq_write')
csv_excel("mix.csv", 'mix')
