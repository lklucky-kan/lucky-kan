from common.infrastructure.server.factory import ServerFactory
from autotest.testLib.base import Base
from autotest.testLib.nic_lib import Iperf
import multiprocessing
import os
import datetime
import subprocess
import time


class Tcp_stress(Base):
    '''

    author: zhuangzhao
    '''

    def __init__(self, **kwargs):
        '''
        testip : test server ip eg: 0.0.0.0 or 0.0.0.0,1.1.1.1
        runtime : The time of the test run
        port : iperf port enabled
        interval : Output is displayed every few seconds
        clientip : client server ip eg: 0.0.0.0 or 0.0.0.0,1.1.1.1
        clientuser : client server user 
        clientpassword : client server password
        speed : Number of enabled threads
        '''
        super().__init__(**kwargs)
        self.server_info = self.options.get('server')
        self.server_obj = self.get_obj(self.server_info.get('ip'))
        self.testip = self.options.get('testip').split(',')
        self.runtime = self.options.get('runtime', '86400')
        self.port = int(self.options.get('port', 10000))
        self.interval = self.options.get('interval', '5')
        self.clientip = self.options.get('clientip').split(',')
        self.clientuser = self.options.get('clientuser')
        self.clientpassword = self.options.get('clientpassword')
        self.speed = self.options.get('speed', 8)
        self.tool = self.options.get('tool', 'iperf')
        self.iperf = Iperf(logpath=self.log_path, tool=self.tool)
        self.reault = True

    def kill_iperf(self, clientip, clientuser, clientpassword):
        # kill test server iperf process and client iperf process
        os.system('pkill -f iperf ')
        os.system(
            f'sshpass -p {clientpassword} ssh -o StrictHostKeyChecking=no {clientuser}@{clientip} "pkill -f iperf "')

    def iperf_process(self, tsip, csip, pkt_lengh=None, side='open_server'):
        # get the current time
        start_time = datetime.datetime.now()
        # Check whether the server or client is enabled on the local server
        if side == "open_server":
            iperf_process = multiprocessing.Process(target=self.iperf.open_server, args=(
                tsip, self.runtime, self.port, self.interval, csip, self.clientuser, self.clientpassword, self.speed, pkt_lengh))
        else:
            iperf_process = multiprocessing.Process(target=self.iperf.open_client, args=(
                tsip, self.runtime, self.port, self.interval, csip, self.clientuser, self.clientpassword, self.speed, pkt_lengh))
        iperf_process.start()
        iperf_process.join()
        self.kill_iperf(self.clientip[0], self.clientuser, self.clientpassword)
        end_time = datetime.datetime.now()
        # Determine whether the process is interrupted based on the running time
        runtime = (end_time - start_time).seconds
        if runtime < int(self.runtime):
            self.iperf.logger.error('iperf is interrupted or not run successful')
            self.reault = False
            return 1
        return 0
    def set_client_mtu(self, csip, network, mtu):
        for net in network:
            os.popen(f'sshpass -p {self.clientpassword} ssh -o StrictHostKeyChecking=no {self.clientuser}@{csip} "ifconfig {net} mtu {mtu}"')
            self.iperf.logger.info(f'client ifconfig {net} mtu {mtu}')

    def iperf_runner(self, sides='open_server'):
        pkt_lengh_list = ['64', '128', '256', '512','680', '1024', '10240']
        # traverse pkt_lengh_list
        for tsip, csip in zip(self.testip, self.clientip):
            network, speeds = self.iperf.get_network_speed(tsip)
            c_network = os.popen(f'sshpass -p {self.clientpassword} ssh -o StrictHostKeyChecking=no {self.clientuser}@{csip} "ls /sys/class/net | egrep -v \'lo|virbr0|docker|veth\'"').read().split()
            print(f'{self.tool} port {self.port} is running')
            for pkt_lengh in pkt_lengh_list:
                if self.iperf_process(tsip, csip, pkt_lengh, sides)==1 and self.port==10000:
                    raise Exception('test is fail , please check it .')
                self.port += 1
            for i in range(3):
                os.system(f'ifconfig {network} mtu 1500')
                self.set_client_mtu(csip, c_network, '1500')
                self.iperf.logger.info(f'ifconfig {network} mtu 1500')
                time.sleep(10)
                self.iperf_process(tsip, csip, pkt_lengh=None, side=sides)
                self.port += 1
                os.system(f'ifconfig {network} mtu 9000')
                self.set_client_mtu(csip, c_network, '9000')
                self.iperf.logger.info(f'ifconfig {network} mtu 9000')
                time.sleep(10)
                self.iperf_process(tsip, csip, pkt_lengh=None, side=sides)
                self.port += 1
            self.set_client_mtu(csip, c_network, '1500')
            os.system(f'ifconfig {network} mtu 1500')
            self.iperf.logger.info(f'ifconfig {network} mtu 1500')

    def test_tcp_stress(self):
        print('test is begain')
        self.iperf_runner('client_client')
        self.iperf_runner()
        if self.reault:
            return {'result': 'pass'}
        else:
            return {'result': 'fail'}

    def test_bidirectional_bandwidth(self):
        print('test is begain')
        start_time = datetime.datetime.now()
        for tsip, csip in zip(self.testip, self.clientip):
            p1 = multiprocessing.Process(target=self.iperf.open_server, args=(
                tsip, self.runtime, self.port, self.interval, csip, self.clientuser, self.clientpassword, self.speed, None, True))
            p2 = multiprocessing.Process(target=self.iperf.open_client, args=(
                tsip, self.runtime, self.port + 1, self.interval, csip, self.clientuser, self.clientpassword, self.speed, None, True))
            p1.start()
            p2.start()
            self.port += 2
        p1.join()
        p2.join()
        self.kill_iperf(self.clientip[0], self.clientuser, self.clientpassword)
        end_time = datetime.datetime.now()
        runtime = (end_time - start_time).seconds
        if runtime > int(self.runtime):
            return {'result': 'pass'}
        else:
            return {'result': 'fail', 'comment': 'iperf is not successful'}
