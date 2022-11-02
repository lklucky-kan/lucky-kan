#!/usr/bin/python3

import sys, os, time
from argparse import ArgumentParser, RawTextHelpFormatter
from os import popen, system
tea_path = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.pardir,
        os.pardir
        )
)
sys.path.append(tea_path)
from common.other.log import Logger
from autotest.testLib.nic_lib import get_nic_ip
from common.file.json_rw import fopen


class Up_down_test():
    '''
    description: this is used to test NIC up down test.
    author: Kail
    '''
    def __init__(self, **kwargs):
        '''
        description: init the class vars
        author: Kail
        params: ip, the ping ip
                cycle, the up down test cycle number
                logger, the logfile
        return: None
        '''
        self.ip = kwargs.get('ip')
        self.cycle = kwargs.get('cycle')
        self.logger = logger


    def pre_env(self):
        '''
        description: clean the test env
        author: Kail
        params: None
        return: None
        '''
        # make sure all NIC have ip
        # nicip_dict = get_nic_ip()
        for k, v in nicip_dict.items():
            if not v['ip']:
                self.logger.warn("nic %s have no ip, show as:\n%s" %(k, v['msg']))
                # sys.exit(-1)
        # clean dmesg log and ping outlet network
        self.logger.info("clear demsg log...")
        popen('dmesg -c')
        self.ping_test()

    def ping_test(self, count=3, para=''):
        '''
        description: clean the test env
        author: Kail
        params: count,  the ping count number
        return: ret, the function return number
        '''
        if diff_vlan is True and para:
            nic = para.split()[-1]
            ping_ip = nicip_dict[nic]['pingip']
        else:
            ping_ip = self.ip
        if diff_vlan and para == '' and type(ping_ip) is list:
            for ip in self.ip:
                self.single_ping(para, ip, count)
        else:
            self.single_ping(para, ping_ip, count)

    def single_ping(self, para, ping_ip, count):
        ret = system('ping %s %s -c %s' %(para, ping_ip, count))
        if ret != 0:
            result["err_msg"].append(
                "ip %s can't ping pass" %ping_ip
            )
            self.logger.error(result["err_msg"][-1])
        else:
            self.logger.info("ip %s can normal ping" %ping_ip)
        return ret

    def up_down_test(self, updown_type):
        '''
        description: single function up/down test
        author: Kail
        params: None
        return: None
        '''
        self.pre_env()
        for i in range(cycle):
            self.logger.info("Starting cycle %s NIC up down test" %i)
            self.updown_action(nicip_dict, updown_type)
            time.sleep(2)
        self.chk_dmesg()


    def nic_updown_test(self):
        '''
        description: nic full cycle up/down test
        author: Kail
        params: None
        return: None
        '''
        self.logger.info(
            '\n' + '*' * 80 + '\n' +
            '%s cycles ifconfig up/down test start' %cycle +
            '\n' + '*' * 80
        )
        self.up_down_test('ifconfig')
        self.logger.info(
            '\n' + '*' * 80 + '\n' +
            '%s cycles ifup/ifdown test start' %cycle +
            '\n' + '*' * 80
        )
        self.up_down_test('ifud')


    def chk_dmesg(self):
        '''
        description: check dmesg log
        author: Kail
        params: None
        return: None
        '''
        dmesg_msg = popen('dmesg').read()
        fopen('dmesg.log', dmesg_msg, 'a')
        dmesg_error = popen('dmesg|grep -iE "error|fail|warn|wrong|bug|respond|pending"')
        if dmesg_error:
            self.logger.error('dmesg info check fail, detail info as below:\n%s' %dmesg_error.read())
        else:
            self.logger.info('dmesg info check pass')


    def updown_action(self, nic_dict, updown_type):
        '''
        description: NIC up and down action
        author: Kail
        params: nic_dict, the nic info dict, eg:
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
                updown_type, the nic up down command type. choices: ['ifconfig', 'ifud']
                    ifconfig: up or down NIC by cmd 'ifconfig' eg:
                        ifconfig NIC up
                        ifconfig NIC down
                    ifud: up or down NIC by cmd 'ifup' or 'ifdown' eg:
                        ifup NIC
                        ifdown NIC
        return: None
        '''
        if updown_type == 'ifconfig':
            up_cmd = 'ifconfig %s up'
            down_cmd = 'ifconfig %s down'
        elif updown_type == 'ifud':
            up_cmd = 'ifup %s'
            down_cmd = 'ifdown %s'
        for nic in nic_dict.keys():
            self.logger.info("Starting "+ "'%s'" %(down_cmd %nic) + "...")
            popen(down_cmd %nic)
        time.sleep(3)
        ret = self.check_network('down', updown_type)
        if ret == 0:
            self.logger.info("NIC all down")
        for nic in nic_dict.keys():
            self.logger.info("Starting" + "'%s'" %(up_cmd %nic) + "...")
            popen(up_cmd %nic)
            time.sleep(3)
            self.ping_test(2, '-I %s' %nic)
        ret = self.check_network('up', updown_type)
        if ret == 0:
            self.logger.info("NIC all up")


    def check_network(self, up_down, updown_cmd):
        '''
        description: check if NIC up/down
        author: Kail
        params: None
        return: ret, 0 is pass and other is fail
        '''
        ret = 0
        ip = self.ip
        ip_dict_tmp = get_nic_ip(nic_list)
        if up_down == 'down':
            for nic, inf in ip_dict_tmp.items():
                if (inf['ip'] and updown_cmd == 'ifud') or (inf['ip'] and updown_cmd == 'ifconfig' and 'RUNNING' in inf['msg'].splitlines()[0]) :
                    result["err_msg"].append(
                        "nic {0} still have ip {1}, down fail".format(nic,inf['ip'])
                    )
                    self.logger.error(result["err_msg"][-1] + '\n' + inf['msg'])
                    ret += 1
                else:
                    self.logger.info('\n' + inf['msg'])
        elif up_down == 'up':
            for nic, inf in ip_dict_tmp.items():
                if not inf['ip']:
                    result["err_msg"].append(
                        "nic {0} have no ip, up fail".format(nic)
                    )
                    self.logger.error(result["err_msg"][-1] + '\n' + inf['msg'])
                    ret += 1
                else:
                    self.logger.info('\n' + inf['msg'])
        return ret



if __name__ == '__main__':
    # parse arguments
    parser = ArgumentParser(
        description='NIC up down test',
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument('-ip', '--pingip',
                        required=True,
                        help='the client ip want to ping'
    )
    parser.add_argument('-c', '--cycle',
                        type=int, default=100,
                        help='the NIC up down cycles number'
    )
    parser.add_argument('-nic', dest='nic',
                        type=str,
                        required=True,
                        help='the NIC port which want to updown'
    )

    group1 = parser.add_argument_group(
        'Ping ip 10.67.13.50, run 200 cycle, do NIC eth1 eth2 test',
        'python %(prog)s ' +
        '-ip 10.67.13.50 ' +
        '-c 200 ' +
        '-nic "eth1 eth2"'
    )
    group2 = parser.add_argument_group(
        'Run 200 cycle, do NIC eth1 eth2 test with different VLAN',
        'python %(prog)s ' +
        '-c 200 ' +
        '-ip "10.67.13.50 192.168.2.10" ' +
        '-nic "eth1 eth2"'
    )


    args = parser.parse_args()
    cycle = args.cycle
    pingip = args.pingip
    nics = args.nic
    nic_list = nics.split(' ')
    logger = Logger(log_file='up_down_test')
    nicip_dict = get_nic_ip()
    for nic in nic_list:
        if nic not in nicip_dict.keys():
            logger.error('NIC %s not exist, please type "ifconfig" check')
            sys.exit(1)
    nicip_dict = get_nic_ip(nic_list)
    if len(nic_list) > 1 and len(pingip.split(' ')) == len(nic_list):
        diff_vlan = True
        pingip = pingip.split(' ')
        for i, nic in enumerate(nic_list):
            nicip_dict[nic]['pingip'] = pingip[i]
    elif len(nic_list) > 1 and len(pingip.split(' ')) != len(nic_list) and len(pingip.split(' ')) != 1:
        print("NIC 数量与 IP 数量不匹配， 详情参看 '-h' 信息")
        sys.exit(-1)
    result = dict()
    result['err_msg'] = []

    if os.path.isfile('dmesg.log'):
        os.remove('dmesg.log')
    test = Up_down_test(ip=pingip, cycle=cycle)
    test.nic_updown_test()
