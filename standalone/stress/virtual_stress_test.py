'''
@Author  :   Zhao.Zhuang
@Contact :   Zhao.Zhuang@luxshare-ict.com
@Software:   TestCase
@Time    :   2022/04/24 
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
'''



from argparse import ArgumentParser, RawTextHelpFormatter
import datetime
import logging
import os
import time
import subprocess

from collections import namedtuple


reports_path = os.popen('pwd').read().strip()
reports_path = reports_path + '/' + 'reports'

def log():
    logger = logging.getLogger()
    fh = logging.FileHandler(f'{reports_path}/reports.log')

    ch = logging.StreamHandler()

    fm = logging.Formatter('%(asctime)s :  %(message)s')

    fh.setFormatter(fm)

    ch.setFormatter(fm)

    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.setLevel("DEBUG")
    return logger


def os_cmd(command):
    """
    Execute OS system command
    :param command: system command can be executed in Linux Shell or Windows Command Prompt
    """

    if not isinstance(command, str):
        raise TypeError(f'command MUST be _cmd string type, {command} is _cmd {type(command)} type')
    SysCMD = namedtuple('SysCMD', ['returncode', 'output'])
    p = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout = p.stdout.decode(encoding='ascii')
    stderr = p.stderr.decode(encoding='ascii')
    output = stdout + stderr
    return SysCMD(p.returncode, output)


def cpu_count():
    rst = os_cmd("lscpu |grep -i '^cpu(s)'|awk '{print $2}'")
    counts = int(rst.output)
    return counts

def mkdir(dirs):
    cmd = f"mkdir -p {dirs}"
    rst = os_cmd(cmd)

def check_stress_run(cpus):
    for i in range(10):
        rst = os_cmd("ps -ef |grep 'bc -l -q |'| grep -v grep |wc -l")
        ps_count = int(rst.output)
        if ps_count == cpus:
            logger.info('process all is running')
            break
        elif i == 4:
            raise Exception('stress process is fail')
        time.sleep(3)


def check_stress_pass():
    for i in range(500):
        rst = os_cmd("ps -ef |grep 'bc -l -q |'| grep -v grep |wc -l")
        ps_count = int(rst.output)
        rst = os_cmd('top -b -n 1|grep -i "cpu(s)"')
        logger.info(f'cpu use {rst.output}')
        if ps_count == 0:
            logger.info('process all is end')#
            break
        elif i == 299:
            raise Exception('stress process is fail')
            
        time.sleep(1)

def run_stress(cpus):
    for i in range(cpus):
        os.popen(f'(time echo "scale=5000; 4*a(1)" | taskset -c {i} bc -l -q | tail -n 1)  >>  {reports_path}/stress_{i}_test.log 2>&1  &')




if __name__== '__main__':
    parser = ArgumentParser(
        description='virtual stress test',
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument('-rt', '--runtime',
                        type=int, default=43200,
                        help="sprict is run time")

    args = parser.parse_args()
    runtime = args.runtime

    cpus = cpu_count()
    if os.path.exists(reports_path):
        print(f'remove {reports_path}')
        os_cmd(f" rm -rf {reports_path}")

    mkdir(reports_path)
    logger = log()

    start_time = starttime = datetime.datetime.now()
    logger.info('======Script start ========')
    end_time = starttime = datetime.datetime.now()
    while (end_time - start_time).seconds < runtime:
        run_stress(cpus)

        check_stress_run(cpus)

        check_stress_pass()

        end_time = starttime = datetime.datetime.now()
    logger.info('======Script end ========')

