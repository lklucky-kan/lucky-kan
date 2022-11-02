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

def chcek_fan(check_key):

    key_list = os_cmd("ipmitool sdr elist | grep -i fan |grep -i percent |awk '{print $9}'").output.split()
    for key in key_list:
        if float(key) < check_key -1 or float(key) > check_key + 1:
            logger.error('set fan speed fail')
            return 1
    logger.info('set fan speed pass')
    

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

def mode1():
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

        speed += 10

    speed = 100
    while speed > 10:

        speed -= 10

        logger.info(f'Set the fan speed to {speed}%')

        os_cmd(f'ipmitool raw 0x3e 0x23 0x00 0x4c 0xa5 1 {speed} {speed} {speed} {speed} {speed} {speed}')

        rts = os_cmd('ipmitool sdr list |grep -i fan ')

        logger.info('save sdr log grep fan')

        logger.info("\n" + rts.output)

        chcek_fan(speed)

        logger.info('sleep 3 s')

        time.sleep(3)

        

def mode2():
    logger.info('Set the fan speed to 100%')

    os_cmd('ipmitool raw 0x3e 0x23 0x00 0x4c 0xa5 1 100 100 100 100 100 100')

    time.sleep(5)

    rts = os_cmd('ipmitool sdr list |grep -i fan ')

    logger.info('save sdr log grep fan')

    logger.info("\n" + rts.output)

    chcek_fan(100)

    logger.info('sleep 30 s')

    time.sleep(30)

    logger.info('Set the fan speed to 10%')

    os_cmd('ipmitool raw 0x3e 0x23 0x00 0x4c 0xa5 1 10 10 10 10 10 10')

    time.sleep(5)

    rts = os_cmd('ipmitool sdr list |grep -i fan ')

    logger.info('save sdr log grep fan')

    logger.info("\n" + rts.output)

    chcek_fan(10)

    logger.info('sleep 30 s')

    time.sleep(30)

def mkdir(dirs):
    cmd = f"mkdir -p {dirs}"
    rst = os_cmd(cmd)

if __name__== '__main__':
    parser = ArgumentParser(
        description='stress fan',
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument('-rt', '--runtime',
                        type=int, default=43200,
                        help="sprict is run time ")

    parser.add_argument('-test_mode1', '--mode1',
                    action='store_true',
                    help='Set the fan speed in increments from 10 to 100')


    parser.add_argument('-test_mode2', '--mode2',
                    action='store_true',
                    help='Set the fan speed to 10 , and Set the fan speed to 100')

    group1 = parser.add_argument_group('help info :','eg : python3 stress_fan.py -rt 100 -test_mode1(or  -test_mode2)')

    args = parser.parse_args()
    runtime = args.runtime

    if os.path.exists(reports_path):
        print(f'remove {reports_path}')
        os_cmd(f" rm -rf {reports_path}")

    mkdir(reports_path)
    logger = log()

    logger.info('='*10 + 'fan stress is running'+ '='*10)

    logger.info('open fan manual mode')

    os_cmd('ipmitool raw 0x3e 0x21 0x00 0x4c 0xa5 1 2')

    module = os_cmd('ipmitool raw 0x3e 0x22 0x00 0x4c 0xa5 1').output.split()

    if module[0] == '02':
        logger.info('open fan manual mode pass')
    else:
        logger.info('open fan manual mode fail')


    start_time = starttime = datetime.datetime.now()

    end_time = starttime = datetime.datetime.now()

    while (end_time - start_time).seconds < runtime:

        if args.mode1:
            mode1()
        
        elif args.mode2:
            mode2()
        
        else:
            raise Exception('Please select a mode to start testing')


        end_time = starttime = datetime.datetime.now()
    
    logger.info('close fan manual mode')

    os_cmd('ipmitool raw 0x3e 0x21 0x00 0x4c 0xa5 1 1')

    module = os_cmd('ipmitool raw 0x3e 0x22 0x00 0x4c 0xa5 1').output.split()

    if module[0] == '01':
        logger.info('close fan manual mode pass')
    else:
        logger.info('close fan manual mode fail')

    logger.info('======Script end ========')



    



