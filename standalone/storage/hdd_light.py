#!/usr/bin/python3

import sys, os, time, re
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



class disk_light():
    '''
    description: this is used to light disk.
    author: Kail
    '''
    def __init__(self, **kwargs):
        '''
        description: init the class vars
        author: Kail
        params: logger, the logfile
        return: None
        '''
        self.logger = kwargs.get('logger') if kwargs.get('logger') else Logger(log_file='disk_light')


    def test(self, dlist, light_color, platform):
        '''
        description: start the light color test
        author: Kail
        params: light_color, the color of light
                dlist, the disk list
        return: None
        '''
        if platform == 'whitley':
            color_cmd = {
                'black': '1bf8',
                'red': '1b78',
                'blueblink': '19f8',
                'redblink': '78'
            }
        else:
            color_cmd = {
                'black' : '13F1',
                'red' : '1371',
                'blueblink' : '11F1',
                'redblink' : '1171'
            }
        for d in disk_list:
            popen('setpci -s {0} 70.w={1}'.format(nvme_dinfo[os.path.basename(d)]['bus_nb'], color_cmd[light_color]))


def nvme_info_dict():
    nvme_infodict = {}
    for line in popen('ls -ld /sys/block/nvme*').read().splitlines():
        dev = re.findall(r'/sys/block/nvme\w+',line)[0].split('/')[-1]
        bdf = re.findall(r'0000:\w{2}:\w+\.\w+',line)[1]
        bus_nb = re.findall(r'0000:\w{2}:\w+\.\w+',line)[0].lstrip('0000:')
        slot_id = popen('lspci -s %s -vvvv | grep -i "Physical Slot"' %bdf).read().split(':')[-1].strip()
        nvme_infodict[dev] = {}
        nvme_infodict[dev]['bdf'] = bdf
        nvme_infodict[dev]['slot'] = slot_id
        nvme_infodict[dev]['bus_nb'] = bus_nb
    return nvme_infodict


if __name__ == '__main__':
    # parse arguments
    parser = ArgumentParser(
        description='hdd light test',
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument('-dt', '--disktype',
                        default='nvme',
                        choices = ['nvme', 'ssd'],
                        help='define the disk type'
    )
    parser.add_argument('-d', '--dev',
                        type=str,
                        help='difine the test disk dev, test all if without this para'
    )
    parser.add_argument('-c', '--color',
                        type=str,
                        required=True,
                        choices = ['black', 'blueblink','red', 'redblink' ],
                        help='define the disk light color' + '\n' +
                             '    black: 灯全灭' +
                             '    blueblink: 蓝灯闪烁' +
                             '    red: 红灯常亮' +
                             '    redblink: 红灯闪烁'
    )
    parser.add_argument('-p', '--platform',
                        type=str,
                        default='palos',
                        help=' whitley or palos '
                        )

    group1 = parser.add_argument_group(
        'Set nvme "nvme0n1 nvme1n1" 蓝灯闪烁',
        'python %(prog)s ' +
        '-d "nvme0n1 nvme1n1" ' +
        '-c blueblink'
    )
    group2 = parser.add_argument_group(
        'Set all nvme 红灯常亮',
        'python %(prog)s ' +
        '-c red'
    )


    args = parser.parse_args()
    dtype = args.disktype
    disk_list = args.dev
    color = args.color
    platform = args.platform

    logger = Logger(log_file='disk_light')

    if dtype == 'nvme':
        nvme_dinfo = nvme_info_dict()
        if disk_list:
            disk_list = [ '/dev/' + d for d in disk_list.split(' ')]
        else:
            disk_list = sorted(list(nvme_dinfo.keys()), key=lambda dev: int(re.findall('nvme\d+', dev)[0].lstrip('nvme')))

    start = disk_light(logger=logger)
    start.test(disk_list, color, platform)
