from multiprocessing.context import SpawnProcess
import os
import re
import time
import datetime
from multiprocessing import Process
from common.other.log import Logger
from common.communication.session import Session
from os import popen

class Iperf(Session):
    '''
    description: This is a iperf class to support iperf connection 
    author: zhuangzhao
    '''

    def __init__(self, **kwargs):
        Session.__init__(self, **kwargs)
        # check iperf tool is install
        self.logpath = kwargs.get('logpath', self.logger.log_file)
        self.tool = kwargs.get('tool', self.logger.log_file)
        iperf_log_file =  os.path.join(self.logpath, 'iperf.log')
        self.logger = Logger(log_file=iperf_log_file, log_file_timestamp=False)
        output = os.popen(f'{self.tool} -v').read().rstrip('\n')
        if 'not found' in output:
            raise Exception(output)

    def get_network_speed(self, ip):
        # Obtain the ID and network speed of a network port
        output = os.popen('ifconfig').read().split('\n\n')
        for network_info in output:
            get_ip = re.findall(ip, network_info, re.M)
            if get_ip:
                network = network_info.split(':')[0]
                speed = re.findall('txqueuelen.*', network_info,
                                   re.M)[0].split(' ')[1]
                speed = int(speed) // 10000 + 1
        return network, speed
    
    def cmd_log_file(self,path ,cmd):
        with open(path, 'a')as fa:
            fa.write(cmd + '\n')


    def open_server(self, testip, runtime, port, interval, clientip, clientuser, clientpassword, speed=None, pkt_length=None, mult=False ):
        network, speeds = self.get_network_speed(testip)
        try:
            if mult :
                cmd = f'{self.tool} -s -i {interval} -p {port} > {self.logpath}/{testip}_{port}_server.log 2>&1 '
            else:
                cmd = f'{self.tool} -s -i {interval} -p {port}  2>&1 '
                self.logger.info(cmd)
            self.cmd_log_file(f'{self.logpath}/cmdlins.log', cmd)
            os.popen(cmd)
            time.sleep(3)
            if pkt_length:
                cmd = f'sshpass -p {clientpassword} ssh -o StrictHostKeyChecking=no {clientuser}@{clientip} "nohup {self.tool}  -c {testip} -i {interval} -P {speed} -p {port} -t {runtime} -l {pkt_length} 2>&1"'
            else:
                cmd = f'sshpass -p {clientpassword} ssh -o StrictHostKeyChecking=no {clientuser}@{clientip} "nohup {self.tool}  -c {testip} -i {interval} -P {speed} -p {port} -t {runtime}  2>&1"'

            output = os.popen(cmd).read()
            if not mult:
                self.logger.info(cmd)
                self.logger.info(f'\n {output}')

            return network,speeds
        except Exception as e:
            self.logger.error(e)
            return network,speeds

    def open_client(self, testip, runtime, port, interval, clientip, clientuser, clientpassword, speed=None, pkt_length=None, mult=False):
        network, speeds = self.get_network_speed(testip)
        try:
            cmd1 = f'sshpass -p {clientpassword} ssh -o StrictHostKeyChecking=no {clientuser}@{clientip} "nohup {self.tool} -s -i {interval} -p {port}  2>&1"'
            os.popen(cmd1)
            time.sleep(3)
            if pkt_length:
                if mult:
                    cmd = f'{self.tool} -c {clientip} -i {interval} -P {speed} -p {port} -t {runtime} -l {pkt_length}  > {self.logpath}/{testip}_{port}_client.log  2>&1'
                else :
                    cmd = f'{self.tool} -c {clientip} -i {interval} -P {speed} -p {port} -t {runtime} -l {pkt_length} 2>&1'
            else:
                if mult :
                    cmd =  f'{self.tool} -c {clientip} -i {interval} -P {speed} -p {port} -t {runtime} > {self.logpath}/{testip}_{port}_client.log  2>&1'
                else:
                    cmd =  f'{self.tool} -c {clientip} -i {interval} -P {speed} -p {port} -t {runtime}   2>&1'
            self.cmd_log_file(f'{self.logpath}/cmdlins.log', cmd)     
            output = os.popen(cmd).read()
            if not mult:
                self.logger.info(cmd1)
                self.logger.info(cmd)
                self.logger.info(f'\n {output}')
            # os.popen(f'echo {cmd} >> {self.logpath}{testip}_{port}_client.log')
            return network,speeds
        except Exception as e:
            self.logger.error(e)
            return network,speeds


def get_nic_ip(nic_list=''):
    '''
    description: get NIC info, include ip, ifconfig infomation
    author: Kail
    return: nic_ip_dict, the nic info dict, eg:
                {
                    'eno1':{
                        'ip': '10.67.13.100',
                        'msg': 'inet 10.67.13.25  netmask 255.255.255.0  broadcast 10.67.13.255
                                inet6 fe80::b27b:25ff:feaf:1da0  prefixlen 64  scopeid 0x20<link>
                                ether b0:7b:25:af:1d:a0  txqueuelen 1000  (Ethernet)
                                RX packets 13568  bytes 2055010 (1.9 MiB)
                                RX errors 0  dropped 179  overruns 0  frame 0
                                TX packets 3937  bytes 547210 (534.3 KiB)
                                TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
                                device interrupt 133'
                    },
                    'eno2':...
                }
    '''
    ip_rgx = '(([01]{0,1}\d{0,1}\d|2[0-4]\d|25[0-5])\.){3}([01]{0,1}\d{0,1}\d|2[0-4]\d|25[0-5])'
    nic_ip_dict = {}
    nics = popen(
        'ls /sys/class/net | egrep -v "lo|virbr0|docker|veth"'
    ).read().strip().split()
    for nic in nics:
        ip_msg = popen(
            "ifconfig %s" %nic
        ).read()
        ip = ''.join([ line.split()[1] for line in ip_msg.splitlines() if 'inet ' in line ])
        nic_ip_dict[nic] = dict()
        nic_ip_dict[nic]['ip'] = ip
        nic_ip_dict[nic]['msg'] = ip_msg
    if nic_list:
        nic_ip_dict = { k:v for k, v in nic_ip_dict.items() if k in nic_list }
    return nic_ip_dict
