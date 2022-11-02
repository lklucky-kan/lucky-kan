import time
import os
import sys
current_path = os.path.abspath(__file__)
father_path = os.path.abspath(
    os.path.dirname(current_path) + os.path.sep + ".")
dir_path = father_path.split('tea')
workpath = dir_path[0] + 'tea'
sys.path.append(workpath)
from common.file.json_rw import fopen
from argparse import ArgumentParser, RawTextHelpFormatter
from autotest.testLib.nic_lib import get_nic_ip

class Nic_driver_update():
    def __init__(self, **kwargs):
        '''
        description: init the class vars
        author: zhuangzhao
        params: logger, the logfile
                ip, the ping ip
                cycles, the drive selftest cycle number
        return: None
        '''
        self.cycles = kwargs.get('cycles')
        self.ip = kwargs.get('ip')
        self.downgrade_path = kwargs.get('downgrade_path')
        self.upgrade_path = kwargs.get('upgrade_path')
        self.log = '/root/nic_reports/nic.log'
        self.errorlog = '/root/nic_reports/error.log'

    def error_log(self, output, cycle=False):
        # format output error info
        if cycle:
            fopen(
                self.errorlog, content=f"S....................................................tarting cycle {cycle} test...", mode='a')
        fopen(self.errorlog, output, 'a')
        fopen(self.log, output, 'a')

    def get_cycle_num(self):
        # Gets the number of times the loop test runs
        self.cyclepath = '/root/nic_reports/nic_cycle.txt'
        cycle = fopen(self.cyclepath)
        cycle = int(cycle)
        return cycle

    def one_cycle_setup(self):
        # When the script is executed for the first time,
        # create the log directory and set the program to start upon startup
        os.system('chmod +x /etc/rc.d/rc.local')
        os.system('cp -r /etc/rc.d/rc.local /etc/rc.d/rc.local_copy')
        if os.path.exists('/root/nic_reports/'):
            os.system('rm -rf /root/nic_reports/')
        os.system('mkdir /root/nic_reports/')
        tea_path = os.popen('pwd').read()
        cmd = f'cd {tea_path}  && python3 standalone/network/nic_drive_update.py -ip {self.ip} -c {self.cycles} -d {self.downgrade_path} -u {self.upgrade_path}'
        fopen('/etc/rc.d/rc.local', content=cmd, mode='a')
        os.system('echo 1 > /root/nic_reports/nic_cycle.txt')
        os.system('touch /root/nic_reports/nic.log')


    def drive_log(self, cycle):
        # Format output log info
        fopen(self.log, "\n\n\n", 'a')
        fopen(self.log, "S..........................tarting cycle %s test..." % cycle, 'a')
        fopen(self.log, '---------------------------this is upgrade test!!!')
        fopen(self.log, "...................................................", 'a')

    def nic_upgrade(self, upgrade_ver, cycle):
        # network drive upgrade
        # f'{upgrade_ver}/mlnxofedinstall --force --distro euleros2.0sp9').read().strip()
        output = os.popen(
            f'{upgrade_ver}/mlnxofedinstall  --without-fw-update --force').read().strip()
        time.sleep(5)
        if 'Installation finished successfully' in output:
            fopen(self.log, 'Installation finished successfully', 'a')
        else:
            self.error_log('upgrade is fail !\n', cycle)
            self.error_log(output)

    def nic_downgrade(self, downgrade_ver, cycle):
        # network drive downgrade
        # f'{downgrade_ver}/mlnxofedinstall --force --distro euleros2.0sp9').read().strip()
        output = os.popen(
            f'{downgrade_ver}/mlnxofedinstall  --without-fw-update --force').read().strip()
        time.sleep(5)
        if 'Installation finished successfully' in output:
            fopen(self.log, 'Installation finished successfully', 'a')
        else:
            self.error_log('downgrade is fail !\n', cycle)
            self.error_log(output)

    def get_nic_drive_ver(self):
        # get network port drive and version info
        time.sleep(10)
        network_ports = get_nic_ip()
        network_dict = {}
        for port in network_ports:
            if network_ports[port]['ip']:
                network_dict[port] = dict()
                network_dict[port]['driver'] = os.popen(
                    "ethtool -i %s |grep driver |awk '{print $2}'" % port).read().strip()
                network_dict[port]['version'] = os.popen(
                    "ethtool -i %s |grep version  |awk '{print $2}'|head -n 1" % port).read().strip()
        return network_dict

    def run_test(self):
        '''
        description: single function up/down test
        author: zhuangzhao
        params: None
        return: None
        '''
        try:
            now_cycle = self.get_cycle_num()
        except Exception as e:
            print(e)
            now_cycle = 0
        if now_cycle == 0:
            self.one_cycle_setup()
            now_cycle = 1
        # If it's singular Verify that the target version was successfully upgraded
        elif now_cycle % 2 == 1:
            fopen('/root/nic_reports/dmesg_upgrade.log',
                  f'---this cycle is {now_cycle} ---', 'a')
            os.system(
                'dmesg | egrep -i "fail|warn|error" >> /root/nic_reports/dmesg_upgrade.log')
            nic_dict = self.get_nic_drive_ver()
            for nic in nic_dict:
                if nic_dict[nic]['version'] in self.upgrade_path:
                    fopen(self.log, 'Upgrade to the target version !', 'a')
                else:
                    self.error_log(
                        'The target version was not upgraded', now_cycle)
            now_cycle += 1
            fopen('/root/nic_reports/nic_cycle.txt', f'{now_cycle}', 'w')

        # If it's even Verify that the target version was successfully degraded
        elif now_cycle % 2 == 0:
            fopen('/root/nic_reports/dmesg_downgrade.log',
                  f'---this cycle is {now_cycle} ---', 'a')
            os.system(
                'dmesg | egrep -i "fail|warn|error" >> /root/nic_reports/dmesg_downgrade.log')
            nic_dict = self.get_nic_drive_ver()
            for nic in nic_dict:
                if nic_dict[nic]['version'] in self.downgrade_path:
                    fopen(self.log, 'Upgrade to the target version !', 'a')
                else:
                    self.error_log(
                        'The target version was not upgraded', now_cycle)
            now_cycle += 1
            fopen('/root/nic_reports/nic_cycle.txt', f'{now_cycle}', 'w')
        self.drive_log(now_cycle)
        network_num = os.popen('lspci | grep -i eth | wc -l').read().strip()
        fopen(
            self.log, f'A total of {network_num} network ports are identified', 'a')
        network_dict = self.get_nic_drive_ver()
        fopen(self.log,'at present cycle  network drive is :', 'a')
        fopen(self.log, network_dict, 'a', True)
        output = os.popen(f'ping -c 2 {self.ip}').read()
        if "100%" in output:
            # ping ip is fail
            fopen(self.errorlog, output, 'a')
        now_cycle = self.get_cycle_num()
        if now_cycle < self.cycles + 1:
            os.system('dmesg -c')
            fopen(self.log, ' clear dmesg log !', 'a')
            if now_cycle % 2 == 1:
                # if it's singular , perform upgrade Tests
                fopen(self.log, ' test is upgrading !', 'a')
                self.nic_upgrade(self.upgrade_path, now_cycle)
            else:
                # if it's even , perform down grade Tests
                fopen(self.log, ' test is downgrading !', 'a')
                self.nic_downgrade(self.downgrade_path, now_cycle)
            time.sleep(5)
            if 'error.log' in  os.listdir('/root/nic_reports/') and now_cycle<3:
                raise Exception('test is fail , please check it')
            os.system('reboot')
            fopen(self.log, ' server is reboot !', 'a')
        else:
            # test clearup
            dirlist = os.listdir('/root/nic_reports/')
            os.system("sed -i '/nic_drive_update.py/d'   /etc/rc.d/rc.local")
            os.system('rm -rf /root/nic_reports/nic_cycle.txt')
            for dir in dirlist:
                if dir == 'error.log':
                    fopen(self.log, '########### test is fail ##########', 'a')
                    fopen(
                        self.log, '########### please check error.log ##########', 'a')
                    return 0
            fopen(self.log, '--------- test is pass  ---------', 'a')


if __name__ == '__main__':
    # parse arguments
    parser = ArgumentParser(
        description='NIC drive self test',
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument('-c', '--cycle',
                        type=int, default=5,
                        help='the NIC drive selftest cycles number'
                        )
    parser.add_argument('-ip', '--pingip',
                        type=str, default='10.67.13.194',
                        help='the client IP which to ping with'
                        )
    parser.add_argument('-d', '--downgrade',
                        type=str, default=' ',
                        help='Root directory for storing upgrade nics'
                        )
    parser.add_argument('-u', '--upgrade',
                        type=str, default=' ',
                        help='Root directory for storing degraded nics'
                        )

    group1 = parser.add_argument_group(
        'Ping ip 10.67.13.50, run 10 cycle',
        'python %(prog)s ' +
        '-ip 10.67.13.50 ' +
        '-c 10'
    )
    args = parser.parse_args()
    pingip = args.pingip
    cycles = args.cycle
    downgrade_path = args.downgrade
    upgrade_path = args.upgrade
    print('!!!!!!  reports path ----> /root/nic_reports/ !!!!!!!!')


    result = dict()
    result['err_msg'] = []
    test = Nic_driver_update(
        cycles=cycles, ip=pingip, downgrade_path=downgrade_path, upgrade_path=upgrade_path)
    try:
        test.run_test()
    except:
        os.system("sed -i '/nic_drive_update.py/d'   /etc/rc.d/rc.local")
        os.system('rm -rf /root/nic_reports/nic_cycle.txt')