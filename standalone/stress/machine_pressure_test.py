'''
@Author  :   Zhao.Zhuang
@Contact :   Zhao.Zhuang@luxshare-ict.com
@Software:   TestCase
@Time    :   2022/04/24
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
'''



from argparse import ArgumentParser, RawTextHelpFormatter
import argparse
from ast import arg
import datetime
import imp
import logging
import multiprocessing
from operator import sub
import os
from re import I, L
import re
import time
import subprocess


from collections import namedtuple

reports_path = os.popen('pwd').read().strip()
reports_path = reports_path + '/' + 'reports'
fio_log = f'{reports_path}/fio'
iperf_log = f'{reports_path}/iperf'
mem_log = f'{reports_path}/memtester'
cpu_log = f'{reports_path}/cpu'
dirlist=["fio" ,"iperf" ]
# dirlist=["fio" ,"iperf" ,"mem" ,"cpu" ]
process_list = []




def log():
    logger = logging.getLogger('reports')
    fh = logging.FileHandler(f'{reports_path}/reports.log')

    ch = logging.StreamHandler()

    fm = logging.Formatter('%(asctime)s :  %(message)s')

    fh.setFormatter(fm)

    ch.setFormatter(fm)

    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.setLevel("DEBUG")
    return logger


def remote_cmd(cmd, ip):
    for i in range(3):
        try:
            user = iperf_user
            password = iperf_password
            client = paramiko.SSHClient()
            # client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=ip, username=user, password=password, timeout=3)
            stdin, stdout, stderr = client.exec_command(cmd)
            output = (stdout.read() + stderr.read()).decode(encoding='ascii').rstrip()
            print(output)
            return output
        except Exception as e :
            logger.error(e)
            logger.info('retry')

def os_cmd(command):
    """
    Execute OS system command
    :param command: system command can be executed in Linux Shell or Windows Command Prompt
    """
    print(command)

    if not isinstance(command, str):
        raise TypeError(f'command MUST be _cmd string type, {command} is _cmd {type(command)} type')
    SysCMD = namedtuple('SysCMD', ['returncode', 'output'])
    p = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20,shell=True)
    stdout = p.stdout.decode(encoding='ascii')
    stderr = p.stderr.decode(encoding='ascii')
    output = stdout + stderr
    return SysCMD(p.returncode, output)

def mkdir(dirs):
    #创建所有文件夹
    for dir in dirs:
        dir = reports_path + "/" + dir
        cmd = f"mkdir -p {dir}"
        rst = os_cmd(cmd)



def chcek_process():
    #检查进程是否全部开启
    status = True
    for key in process_list:
        count = os_cmd(f'ps -ef | grep -v grep | grep -c {key}').output
        for i in range(3000):
            if key == 'iperf':
                if int(count) != len(nic_name) * 2:
                    time.sleep(5)
                    print(count)
                    if i == 2:
                        status = False
                    else:
                        continue
            if int(count) <= 1:
                logger.error(f'run {key} is fail')
                time.sleep(5)

                if i == 2:
                    status = False
                else:
                    continue

    if status:
        logger.info('run all process pass')
    else:
        raise Exception('run all process is fail')

def kill_process():
    # 关闭所有进程
    status = True
    for key in process_list:
        os_cmd(f'pkill -8 {key}')
        if key == 'iperf':
            if not loop:
                remote_cmd(f'pkill -8 {key}')
                time.sleep(10)
                count = remote_cmd(f'ps -ef | grep -v grep | grep -c {key}').output
                if int(count) != 0:
                    status = False
                    logger.error(f'kill remote {key} is fail')
        time.sleep(5)
        for i in range(3):
            count = os_cmd(f'ps -ef | grep -v grep | grep -c {key}').output
            if int(count) != 0:
                logger.error(f'kill {key} is fail')
                time.sleep(5)
                if i == 2:
                    status = False
            else:
                break
    if status:
        logger.info('kill all process pass')


def stress_fio(dict):
    # 本机开启fio
    dev = dict['dev']
    ts = dict['ts']
    cmd = f'fio --name={dev} --direct=1 --ioengine=libaio \
            --time_based=1 --end_fsync=1 \
            --group_reporting --log_avg_msec=60000 \
            --bwavgtime=60000 --numjobs=1 \
            --iodepth=32 --rw=randrw --rwmixread=50 --bs=4k \
            --runtime={ts} --filename=/dev/{dev} 2>&1 >> {fio_log}/fio_{dev}.log '
    logger.info(f'cmd : {cmd}' )
    os_cmd(cmd)

def iperf_server(dict):
    # 在远端启iperf server
    port = dict['port']
    iperf_ip = dict['ip']
    cmd = f"iperf -s -i 5 -l 1024k -P 5 -p 500{port}"
    if loop :
        logger.info(f'cmd : {cmd}' )
        os_cmd(cmd)
    else:
        logger.info(f'remotecmd : {cmd}' )
        remote_cmd(cmd, iperf_ip)


def iperf_client(dict):
    #本地开启iperf client
    port = dict['port']
    iperf_ip = dict['ip']
    cmd = f'iperf -c {iperf_ip} -i 5 -l 1024k -t {runtime} -P 5 -p 500{port} 2>&1 >> {iperf_log}/iperf_port_500{port}_client.log '
    logger.info(f'cmd : {cmd}')
    os_cmd(cmd)

def stress_cpu(dict):
    cmd = "lscpu |grep -i '^cpu' |awk '{print $2}'"
    rst = os_cmd(cmd).output.strip()
    cpu_count = int(rst) -4
    cmd = f"stress-ng -c {cpu_count} -t {runtime}"
    logger.info(cmd)
    os_cmd(cmd)


def stress_mem(dict):
    #开启memtester
    cmd = " free -g |grep -i mem |awk '{print $4}' "
    rst = os_cmd(cmd).output.strip()
    mem = int(rst) * 0.85
    mem = int(mem)
    cmd = f"stress-ng --vm 20 --vm-bytes {mem}G --vm-keep -t {runtime}"
    logger.info(cmd)
    os_cmd(cmd)

def loop_iperf(dict):
    #开启loop iperf
    _nic_name_list = dict['nic_name']
    port = 6030
    for _nic_names in _nic_name_list:
        cmd = f"nohup iperf -B {nic_dict[_nic_names[1]]['ip']} -s -p {port}  2>&1 &"
        logger.info(cmd)
        os.popen(cmd)
        cmd = f"nohup iperf -B {nic_dict[_nic_names[0]]['ip']} -c {nic_dict[_nic_names[1]]['ip_client']}  -t {runtime} -i 5 -p {port} -P 4 2>&1 &"
        logger.info(cmd)
        os.popen(cmd)
        port += 1

def check_iperf_loop_test(dict):
    logger.info('check iperf test is run')
    _nic_name_list = dict['nic_name']
    port = 4030
    for _nic_names in _nic_name_list:
        cmd = f"nohup iperf -B {nic_dict[_nic_names[1]]['ip']} -s -p {port}  2>&1 &"
        logger.info(cmd)
        os.popen(cmd)
        cmd = f"iperf -B {nic_dict[_nic_names[0]]['ip']} -c {nic_dict[_nic_names[1]]['ip_client']}  -t 5 -i 2 -p {port} -P 4 "
        logger.info(cmd)
        rst = os_cmd(cmd).output.strip()
        if 'connected' not in rst:
            raise Exception(f'{_nic_names} iperf fail')
        port += 1
    os.popen('pkill -8 iperf')

def nic_mac(ports):
    for port in ports:
        for name in port:
            cmd = "ifconfig %s |grep ether |awk '{print $2}'" % name
            rst = os_cmd(cmd).output.strip()
            nic_dict[name] ={'mac':rst}


def set_loop_route(nic_names_list):
    cmd ='iptables -t nat -F'
    # os_cmd(cmd)
    logger.info('clear nat list')
    num_1 = 100
    for _nic_names in nic_names_list:
        ip_0 = f'192.168.{num_1}.1'
        ip_1 = f'192.168.{num_1+1}.1'
        ip_2 = f'192.168.{num_1+2}.1'
        ip_3 = f'192.168.{num_1+3}.1'
        nic_dict[_nic_names[0]]['ip'] = ip_0
        nic_dict[_nic_names[0]]['ip_client'] = ip_2
        nic_dict[_nic_names[1]]['ip'] = ip_1
        nic_dict[_nic_names[1]]['ip_client'] = ip_3

        #set ip
        cmd = f'ifconfig {_nic_names[0]} 100.100.100.1/24'
        os_cmd(cmd)
        cmd = f'ifconfig {_nic_names[0]} {ip_0}/24'
        os_cmd(cmd)
        cmd = f'ifconfig {_nic_names[1]} 100.100.100.2/24'
        os_cmd(cmd)
        cmd = f'ifconfig {_nic_names[1]} {ip_1}/24'
        os_cmd(cmd)
        cmd = f'iptables -t nat -A POSTROUTING -s {ip_0} -d {ip_3} -j SNAT  --to-source {ip_2}'
        os_cmd(cmd)
        cmd = f'iptables -t nat -A PREROUTING -d {ip_2} -j DNAT --to-destination {ip_0}'
        os_cmd(cmd)
        cmd = f'iptables -t nat -A POSTROUTING -s {ip_1} -d {ip_2} -j SNAT  --to-source {ip_3}'
        os_cmd(cmd)
        cmd = f'iptables -t nat -A PREROUTING -d {ip_3} -j DNAT --to-destination {ip_1}'
        os_cmd(cmd)
        cmd = f'ip route add {ip_3} dev {_nic_names[0]}'
        os_cmd(cmd)
        cmd = f'ip route add {ip_2} dev {_nic_names[1]}'
        os_cmd(cmd)

        cmd = f'arp -i {_nic_names[0]}  -s {ip_3} {nic_dict[_nic_names[1]]["mac"]}'
        os_cmd(cmd)
        cmd = f'arp -i {_nic_names[1]}  -s {ip_2} {nic_dict[_nic_names[0]]["mac"]}'
        os_cmd(cmd)
        num_1 += 10


class Process(object):

    def __init__(self, dev_list) -> None:
        self.pool = multiprocessing.Pool(len(dev_list)+15)

    def run_process(self, funcname, *args, **kwargs):

        self.pool.apply_async(func=funcname,args=(kwargs, ) )

if __name__== '__main__':
    parser = ArgumentParser(
        description='machine pressure test',
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument('-rt', '--runtime',
                        type=int, default=43200,
                        help="sprict is run time second")

    parser.add_argument('-st', '--sleeptime',
                    type=int, default=0,
                    help="sprict is idle time second")

    parser.add_argument('-FIO', '--stress_fio',
                    action='store_true',
                    help='')

    parser.add_argument('-IPERF', '--stress_iperf',
                    action='store_true',
                    help='')

    parser.add_argument('-MEM', '--stress_mem',
                    action='store_true',
                    help='')
    parser.add_argument('-LOOP', '--iperf_loop',
                    action='store_true',
                    help='')

    parser.add_argument('-CPU', '--stress_cpu',
                    action='store_true',
                    help='')

    parser.add_argument('-IPERFIP', '--iperf_ip',
                        type=str,
                        help="client ip eg : '192.168.1.1;192.....' ")
    parser.add_argument('-IPERFUSER', '--iperf_user',
                        type=str,
                        help="client user ")
    parser.add_argument('-IPERFPASSWD', '--iperf_passwd',
                        type=str,
                        help="client password")# Loop
    parser.add_argument('-NICNAME', '--nic_name',
                    type=str, default='',
                    help="sprict is idle time second")


    group1 = parser.add_argument_group('help info :',"eg : python3  machine_pressure_test.py -rt 3600 -st 10 -FIO -MEM -CPU -IPERF -IPERFIP '10.57.54.33' -IPERFUSER 'root' -IPERFPASSWD '1'")
    group1 = parser.add_argument_group('help info :',"eg : python3  machine_pressure_test.py -rt 3600 -st 10 -FIO -MEM -CPU -LOOP  -NICNAME '[[\"ens41\",\"ens51\"], [\"ens11f0np0\",\"ens11f1np1\"],[\"ens21f0np0\",\"ens21f1np1\"],[\"ens33f0np0\",\"ens33f1np1\"]]'")

    iperf_port= [10,11]

    args = parser.parse_args()
    runtime = args.runtime
    sleeptime = args.sleeptime
    fio = args.stress_fio
    iperf = args.stress_iperf
    mem = args.stress_mem
    cpu = args.stress_cpu
    nic_dict ={}
    if iperf:
        import paramiko
        iperf_ip_list = args.iperf_ip.split(';')
        iperf_user = args.iperf_user
        iperf_password = args.iperf_passwd
    loop =args.iperf_loop
    if loop:
        nic_name = args.nic_name
        nic_name = eval(nic_name)
        nic_list = os_cmd( "ls /sys/class/net/ | grep -Ev 'docker|lo|virbr'").output.strip().split()
        for nic in nic_name:
            if nic[0] not in nic_list:
                raise Exception(f'not found nic port name : {nic[0]}')
            if nic[1] not in nic_list:
                raise Exception(f'not found nic port name : {nic[0]}')
        print('check nic port is pass')


    os_drive=os_cmd("df | grep -E '/boot/efi|/boot|/$' | awk '{print $1}' | grep -Eo 'sd[a-z]+|nvme\w+n\w' |uniq").output.strip()
    # drives_sata=os_cmd("grep -P 'sd\w+$' /proc/partitions | grep -Pv '\d+$' | grep -vE 'usb|%s' | awk '{print $NF}'"% os_drive).output.split()
    # drives_nvme=os_cmd("grep -P 'nvme\w+$' /proc/partitions | grep -Pv 'p\d+$' | grep -vE 'usb|%s' | awk '{print $NF}'"% os_drive).output.split()
    # drives_list = drives_sata + drives_nvme
    drives_list = os_cmd("lsblk |grep -i disk |awk '{print $1}'").output.strip().split()


    if os_drive in drives_list:
        drives_list.remove(os_drive)
    if not drives_list:
        drives_list = [0,0,0,0]

    if os.path.exists(reports_path):
        print(f'remove {reports_path}')
        os_cmd(f" rm -rf {reports_path}")

    mkdir(dirlist)
    logger = log()
    start_time = time.perf_counter()
    logger.info('======Script start ========')
    if fio :
        print(f'fio test disk is {drives_list}')
        choose = input('please check test disk is true (Y/N):')
        if choose.lower() != 'y':
            exit()
    if loop:
        nic_mac(nic_name)
        set_loop_route(nic_name)
        dict1 = {'nic_name': nic_name}
            # loop_iperf(dict1)
        check_iperf_loop_test(dict1)




    while runtime > 0:
        #创建进程池
        start_time = time.perf_counter()
        p = Process(drives_list)

        if fio :
            logger.info('fio is running ')
            if 'fio' not in process_list:
                process_list.append('fio')
            for dev in drives_list:
                p.run_process(funcname=stress_fio, dev=dev, ts=runtime)


        if iperf:
            port = 0
            logger.info('iperf remote test is running ')
            iperf_ts = runtime
            if 'iperf' not in process_list:
                process_list.append('iperf')
            for ip in iperf_ip_list:
                p.run_process(funcname=iperf_server, port=port, ip=ip)
                time.sleep(3)
                p.run_process(funcname=iperf_client, port=port, ip=ip)

        if mem:
            logger.info('memtester is running ')
            if 'stress-ng' not in process_list:
                process_list.append('stress-ng')
            p.run_process(funcname=stress_mem, mem=mem)

        if cpu:
            logger.info('stress cpu  is running ')
            if 'stress-ng' not in process_list:
                process_list.append('stress-ng')
            p.run_process(funcname=stress_cpu, cpu=cpu)

        if loop:
            dict1 = {'nic_name': nic_name}
            # loop_iperf(dict1)
            logger.info('iperf loop test is running ')
            if 'iperf' not in process_list:
                process_list.append('iperf')
            #p.run_process(funcname=loop_iperf, nic_name=nic_name)

            loop_iperf(dict1)
        p.pool.close()
        cycletime = time.perf_counter()
        time.sleep(5)
        chcek_process()


        if sleeptime !=0:
            logger.info('Dynamic Load Testing')
            time.sleep(sleeptime)
            end_time = time.perf_counter()

        else:
            logger.info('Machine load test')
            while runtime>0:
                start_time = time.perf_counter()
                time.sleep(60)
                end_time = time.perf_counter()
                logger.info(f'run: {(end_time - start_time)}')
                runtime = runtime - (end_time - start_time)
                print(f'runtime : {runtime}')

        p.pool.terminate()
        kill_process()
        if sleeptime !=0:
            time.sleep(sleeptime)
        p.pool.join()
        logger.info(f'run: {(end_time - start_time)}')
        runtime = runtime - (end_time - start_time)
        print(f'runtime : {runtime}')
    logger.info('======Script end ========')
