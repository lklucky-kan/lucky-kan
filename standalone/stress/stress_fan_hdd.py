from argparse import ArgumentParser, RawTextHelpFormatter
from calendar import c
import datetime
import logging
import os
from statistics import mode
import time
import subprocess
import multiprocessing

from collections import namedtuple

reports_path = os.popen('pwd').read().strip()
reports_path = reports_path + '/' + 'reports'

class Process(object):

    def __init__(self, dev_list) -> None:
        self.pool = multiprocessing.Pool(len(dev_list)+6)
    
    def run_process(self, disk,  rwmode, blk_size, queue_depth, speed, default=False):
    
        self.pool.apply_async(func=fio_run,args=(disk, rwmode, blk_size, queue_depth, speed, default) )

def chcek_fan(check_key):

    key_list = os_cmd("ipmitool sdr elist | grep -i fan |grep -i percent |awk '{print $9}'").output.split()
    for key in key_list:
        if float(key) < check_key -1 or float(key) > check_key + 1:
            logger.error('set fan speed fail')
            return 1
    logger.info('set fan speed pass')
    

def chcek_process():
    #检查进程是否全部开启
    status = True
    time.sleep(3)
    
    count = os_cmd(f'ps -ef | grep -v grep | grep -c fio').output.strip()
    if int(count) <= 1:
        status = False
        logger.error(f'run fio is fail')
    if status:
        logger.info('run all process pass')

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

def fio_run(disk, rwmode, blk_size, queue_depth, speed, default='Baseline_fio', jobs=1  ):
    now_time = time.strftime("%a %b %d %H:%M:%S %Y",time.localtime())
    cmd = f'echo ======== {now_time} ========= >> {reports_path}/{disk}/{default}_{rwmode}.log'
    rst = os_cmd(cmd)
    cmd = f'echo ========set fan {speed}%========= >> {reports_path}/{disk}/{default}_{rwmode}.log'
    rst = os_cmd(cmd)
    fio_cmd = f'fio --name={disk}_test --filename=/dev/{disk} --ioengine=libaio --direct=1 --thread=1 --numjobs={jobs} --iodepth={queue_depth} --rw={rwmode} --bs={blk_size}k --runtime=120 --time_based=1 --size=100% --norandommap=1 --randrepeat=0 --group_reporting --log_avg_msec=1000 --bwavgtime=1000  >> {reports_path}/{disk}/{default}_{rwmode}.log'
    logger.info(fio_cmd)
    rst = os_cmd(fio_cmd)
    if rst.returncode == '0':
        print('run pass')

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

def fio_default(disk_list, rwmode, bs, qd ,speed):
    for disk in disk_list:
        dev = disk.split('/')[-1]
        p = Process(disk_list)
        p.run_process(dev, rwmode, bs, qd, speed,'performance')
        for cdisk in disk_list:
            if cdisk != disk:
                cdev = cdisk.split('/')[-1]
                p.run_process(cdev, 'randread', '4', '1', 'default', speed)
        p.pool.close()
        chcek_process()
        p.pool.join()




def mode1(disk_list, speed=10):
    logger.info(f'Set the fan speed to {speed}%')

    os_cmd(f'ipmitool raw 0x3e 0x23 0x00 0x4c 0xa5 1 {speed} {speed} {speed} {speed} {speed} {speed}')

    rts = os_cmd('ipmitool sdr list |grep -i fan ')

    logger.info('save sdr log grep fan')

    logger.info("\n" + rts.output)

    chcek_fan(speed)

    for disk in disk_list:
        dev = disk.split('/')[-1]
        fio_run(dev, 'write', '256', '8', speed)
        fio_run(dev, 'randwrite', '4', '8', speed)
        fio_run(dev, 'read', '256', '8', speed)
        fio_run(dev, 'randread', '4', '8', speed)

        

def mode2(disk_list, speed=10):
    speed =10
    while speed <= 100:
        logger.info(f'Set the fan speed to {speed}%')

        os_cmd(f'ipmitool raw 0x3e 0x23 0x00 0x4c 0xa5 1 {speed} {speed} {speed} {speed} {speed} {speed}')

        rts = os_cmd('ipmitool sdr list |grep -i fan ')

        logger.info('save sdr log grep fan')

        logger.info("\n" + rts.output)

        chcek_fan(speed)

        logger.info('sleep 3 s')

        time.sleep(3)
        
        logger.info(' run fio mode is write')
        fio_default(disk_list, 'write', '256', '8' , speed)
        logger.info(' run fio mode is randwrite')
        fio_default(disk_list, 'randwrite', '4', '8' , speed)
        logger.info(' run fio mode is read')
        fio_default(disk_list, 'read', '256', '8' , speed)
        logger.info(' run fio mode is randread')
        fio_default(disk_list, 'randread', '4', '8' , speed)

        speed += 10








def mkdir(dirs):
    cmd = f"mkdir -p {dirs}"
    rst = os_cmd(cmd)


if __name__== '__main__':
    parser = ArgumentParser(
        description='stress fan hdd',
        formatter_class=RawTextHelpFormatter
    )

    parser.add_argument('-test_mode1', '--mode1',
                    action='store_true',
                    help='Turn the fan to the lowest speed and run fio across all disks')


    parser.add_argument('-test_mode2', '--mode2',
                    action='store_true',
                    help='Turn the fan to the lowest speed, then increase it by 10 each time and run fio on all disks')

    group1 = parser.add_argument_group('help info :','eg : python3 stress_fan.py  -test_mode1(or  -test_mode2  ) ')

    args = parser.parse_args()

    if os.path.exists(reports_path):
        print(f'remove {reports_path}')
        os_cmd(f" rm -rf {reports_path}")

    mkdir(reports_path)
    logger = log()

    disk_list = os_cmd(
                " fdisk -l |grep -iEo 'Disk /dev/sd[a-z]+|Disk /dev/nvme\w+n\w' | awk '{print $2}'"
            ).output.split()
    os_dev = os_cmd(
        "df |grep -i /boot | awk '{print $1}' | grep -Eo '/dev/sd[a-z]+|/dev/nvme\w+n\w'  | head -n1"
    ).output.strip()
    disk_list.remove(os_dev)

    logger.info('='*10 + ' stress fan hdd is running'+ '='*10)

    logger.info('open fan manual mode')

    os_cmd('ipmitool raw 0x3e 0x21 0x00 0x4c 0xa5 1 2')
    

    module = os_cmd('ipmitool raw 0x3e 0x22 0x00 0x4c 0xa5 1').output.split()

    if module[0] == '02':
        logger.info('open fan manual mode pass')
    else:
        logger.info('open fan manual mode fail')

    for disk in disk_list:
        dev = disk.split('/')[-1]
        path = reports_path + '/' + dev
        mkdir(path)

    if args.mode1:
        mode1(disk_list)
    
    if args.mode2:
        mode2(disk_list)

    logger.info('close fan manual mode')

    os_cmd('ipmitool raw 0x3e 0x21 0x00 0x4c 0xa5 1 1')

    module = os_cmd('ipmitool raw 0x3e 0x22 0x00 0x4c 0xa5 1').output.split()

    if module[0] == '01':
        logger.info('close fan manual mode pass')
    else:
        logger.info('close fan manual mode fail')

    logger.info('======Script end ========')
