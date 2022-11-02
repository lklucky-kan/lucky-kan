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
import json

from json import dumps
from collections import namedtuple

workpath = os.path.dirname(os.path.abspath(__file__))
reports_path = workpath + '/' + 'reports'
log = reports_path + '/' + 'HBA_drive.log'
fail_log = reports_path + '/' + 'HBA_drive_fail.log'
cyclelog = reports_path + '/' + 'cycle.log'

def fopen(file='', content='', mode='r', json=False):
    '''
    description: read or write file
    author: zhuangzhao
    params: file, the file want to operate.
            content, the msg that want to be written to file.
            mode, the open file mode, choose from [r, w, a]
            json, use when deal json date, choices:[True, False]
    return: data, the file's reading date
    '''
    # transfer dat file to dat_dict
    now = time.strftime("%a %b %d %H:%M:%S %Y",time.localtime())
    data = ''
    print(content)
    f = open(file, mode, encoding='UTF-8')
    if mode == 'w' or mode == 'a':
        if json:
            f.write(dumps(content, indent=4, sort_keys=False) + '\n')
        else:
            f.write(now + " : " + content + "\n")
    else:
        if json:
            data = eval(f.read())
        else:
            data = f.read()
    f.close()
    return data


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

def download_bios(file):
    cmd = f'/opt/MegaRAID/storcli/storcli64 /c0 download bios file={file}'
    fopen(file=log, content=cmd, mode='a')
    rst = os_cmd(cmd)
    out = str(rst.output)
    # if 'successful' in out:
    #     info = 'HBA card drive download command is successful'
    #     fopen(file=log, content=info, mode='a')
    # else:
    #     info = 'HBA card drive download command is fail'
    #     fopen(file=fail_log, content=info, mode='a')


def download_fw(file):
    cmd = f'/opt/MegaRAID/storcli/storcli64 /c0 download file={file} noverchk'
    fopen(file=log, content=cmd, mode='a')
    rst = os_cmd(cmd)
    out = str(rst.output)
    # if 'successful' in out:
    #     info = 'HBA card drive download command is successful'
    #     fopen(file=log, content=info, mode='a')
    # else:
    #     info = 'HBA card drive download command is fail'
    #     fopen(file=fail_log, content=info, mode='a')

def check_fw_version(ver):
    rst = os_cmd(' /opt/MegaRAID/storcli/storcli64 /c0 show j ')
    out = str(rst.output)
    fw_ver = json.loads(out)["Controllers"][0]["Response Data"]["FW Version"]
    if fw_ver == ver:
        info = f'check fw version is pass now version : {fw_ver}'
        fopen(file=log, content=info, mode='a')
    else:
        info = f'check fw version is fail now version : {fw_ver} , target version {ver}'
        fopen(file=fail_log, content=info, mode='a')
def check_bios_version(ver):
    ver = '_'+ver
    rst = os_cmd(' /opt/MegaRAID/storcli/storcli64 /c0 show j ')
    out = str(rst.output)
    bios_ver = json.loads(out)["Controllers"][0]["Response Data"]["BIOS Version"]
    if bios_ver == ver:
        info = f'check bios version is pass now version : {bios_ver}'
        fopen(file=log, content=info, mode='a')
    else:
        info = f'check bios version is fail now version : {bios_ver} , target version {ver}'
        fopen(file=fail_log, content=info, mode='a')

def mkdir(dirs):
    cmd = f"mkdir -p {dirs}"
    rst = os_cmd(cmd)

def get_cycle():
    rst = os_cmd(f'cat {cyclelog}')
    cycle = rst.output.strip()
    cycle = int(cycle)
    return cycle


if __name__ == "__main__" :
    parser = ArgumentParser(
    description='HBA FW BIOS update test ',
    formatter_class=RawTextHelpFormatter
    )
    parser.add_argument('-c', '--cycle',
                        type=int, default=20,
                        help="sprict is run cycle ")

    parser.add_argument('-fwdpath', '--downloadpath',
                        type=str, required=True,
                        help="The root directory where the downgrade files are located ")


    parser.add_argument('-fwupath', '--updatepath',
                        type=str, required=True,
                            help="The root directory where the upgraded files are located")

    parser.add_argument('-downver', '--downloadversion',
                        type=str, required=True,
                        help="Check the parameters after the fw downgrade")

    parser.add_argument('-updatever', '--updateversion',
                        type=str, required=True,
                        help="Check the parameters after the fw upgrade")


    parser.add_argument('-biosdpath', '--biosdownloadpath',
                        type=str, required=True,
                        help="The root directory where the downgrade files are located ")

    parser.add_argument('-biosupath', '--biosupdatepath',
                        type=str, required=True,
                            help="The root directory where the upgraded files are located")

    parser.add_argument('-ND', '--notdefault',
                        action='store_true',
                    help='not is one cycle')

    group1 = parser.add_argument_group('help info :','eg : python3 hba_fw_update.py -c 2 -dpath "/root/HBA_9/9500P17_MIUEFI/Firmware/..bin" '+
                                                        '-upath "/root/HBA_9/9500P18_MIUEFI/Firmware/..bin"' +
                                                        '-downver "17.00.00.00" ' +
                                                        '-updatever "18.00.00.00"' +
                                                        '-biosdpath "...." '+
                                                        '-biosupath "...." ')

    args = parser.parse_args()

    test_cycle = args.cycle
    dpath = args.downloadpath
    upath = args.updatepath
    downver = args.downloadversion
    updatever = args.updateversion
    biosdpath = args.biosdownloadpath
    biosupath = args.biosupdatepath

    if not args.notdefault:
        os_cmd("sed -i '/hba_fw_update/d' /etc/rc.local")
        if os.path.exists(reports_path):
            print(f'remove {reports_path}')
            os_cmd(f" rm -rf {reports_path}")
        mkdir(reports_path)
        os_cmd(f'echo python3 {workpath}/hba_fw_update.py -c {test_cycle} -fwdpath "{dpath}" -fwupath "{upath}" -downver "{downver}" -updatever "{updatever}" -biosdpath "{biosdpath}" -biosupath "{biosupath}"  -ND >> /etc/rc.local' )
        os_cmd(f'echo 1 > {cyclelog}')


    #确认是否是第一圈
    cycle = get_cycle()

    if cycle > test_cycle:
        info = f'==========={cycle} cycle test is finsh ============'
        fopen(file=log, content=info, mode='a')
        os_cmd("sed -i '/hba_fw_update/d' /etc/rc.local")
        exit()
    info = f'========= {cycle} cycle test ============'
    fopen(file=log, content=info, mode='a')

    if args.notdefault:
        if cycle % 2 == 1:
            check_bios_version(downver)

        else:
            check_bios_version(updatever)

    if cycle % 2 == 1:
        download_fw(upath)
        time.sleep(5)
        check_fw_version(updatever)
        download_bios(biosupath)
        check_bios_version(updatever)
    else:
        download_fw(dpath)
        time.sleep(5)
        check_fw_version(downver)
        download_bios(biosdpath)
        check_bios_version(downver)

    rst = os_cmd(' /opt/MegaRAID/storcli/storcli64 /c0 show ')
    info = '\n' + rst.output
    fopen(file=log, content=info, mode='a')
    

    cycle += 1
    os_cmd(f'echo {cycle} > {cyclelog}')
    info = 'reboot cycle'
    fopen(file=log, content=info, mode='a')

    os_cmd('reboot')
