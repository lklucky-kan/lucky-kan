import subprocess
import argparse
import sys
import os
import time
import re
import shutil
tea_path = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.pardir,
        os.pardir
        )
)
sys.path.append(tea_path)
if re.search(r'%s' % os.path.abspath('.'), os.path.dirname(__file__), re.I):
    baselocallogpath = os.path.dirname(__file__)
else:
    if os.path.dirname(__file__).split('/')[0] != '':
        baselocallogpath = os.path.abspath('.') + "/" + os.path.dirname(__file__)
    else:
        baselocallogpath = os.path.abspath('.') + os.path.dirname(__file__)

scriptdir = baselocallogpath
class Cpld_Cycle():
    '''
    author :wanglei
    description :for palos MLB cpld cycle test
    params : self.cyclecount   : cpld test cycle count
             self.updatash     : for palos cpld updata.sh path
             self.updatafile   : cpld up FW file.jed
             self.downfile     : cpld down FW file.jed
    '''

    def __init__(self,count,updatash,updatafile,upver,downfile,downver):
        self.cyclecount = count
        self.updatash = updatash
        self.updatafile = updatafile
        self.downfile = downfile
        logdir = os.path.dirname(os.path.realpath(__file__)) + "/cpld-updata"
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        else:
            shutil.rmtree(logdir)
            os.makedirs(logdir)
        self.logpath = logdir + "/cpld-updata.log"
        self.log_filter_path = scriptdir.split('standalone')[0] + 'standalone/common_test/log-parser/'
        self.sxflag = ''
        initver = subprocess.getstatusoutput("ipmitool raw 0x36 1 0xdf 0xdd 0 2 |grep -ivE 'Unknown|unexpected' |head -n1 |awk -F ' ' '{print $2}'")[1]
        base10 = int('%s' % initver,16)
        ascllv = chr(int(base10))

        if str(ascllv) == downver.split('0')[-1]:
            self.sxflag = True
        elif str(ascllv) == upver.split('0')[-1]:
            self.sxflag = False

    def log_save(self,msg=None):
        '''
        description: save flush cpld cycle test log
        '''
        with open(self.logpath,'a') as f:
            if msg == None:
                f.write('\n')
            else:
                f.write(msg)
                f.write('\n')

    def system_log_act(self,act):
        '''
        description:collect or clear system log use standlone/comman_test/log-parser/log_parser.py
        '''
        if act == 'clear':
            print('python3 %slog_parser.py --b' % self.log_filter_path)
            subprocess.getstatusoutput('python3 %slog_parser.py --b' % self.log_filter_path)
        elif act == 'save':
            print('python3 %slog_parser.py --a' % self.log_filter_path)
            subprocess.getstatusoutput('python3 %slog_parser.py --a' % self.log_filter_path)

    def cpld_check(self,check):
        '''
        description:use ipmitool get MLB cpld fw version
        '''
        checkres = subprocess.getstatusoutput("ipmitool raw 0x36 1 0xdf 0xdd 0 2 |grep -ivE 'Unknown|unexpected' |head -n1")[1]
        if check == 'before':
            self.log_save(msg="##########before mlb cpld version######")
        elif check == 'after':
            self.log_save(msg="##########after mlb cpld version######")
        self.log_save(msg=checkres)
        return checkres

    def check_Yafuflash(self):
        '''
        description:check after flush cpld ,the tool Yafuflash if end
        '''
        while True:
            yhpe = subprocess.getstatusoutput('ps -e |grep -i Yafuflash')[1]
            if yhpe == "":
                break
            else:
                time.sleep(5)

    def cpld_action(self,act):
        '''
        description:according act=up or act=down select up cpld or down cpld
        '''
        if act == 'up':
            self.log_save(msg="Start up MLB cpld")
            cmd = '%s/Update.sh -kcs -cs 0x81 -nr -fb -d 4 %s' % (self.updatash,self.updatafile)
            self.log_save(msg=cmd)
            os.chdir(self.updatash)
            print("Start up MLB cpld")
            upres = subprocess.getstatusoutput('%s/Update.sh -kcs -cs 0x81 -nr -fb -d 4 %s' % (self.updatash,self.updatafile))[1]
            if re.search(r'Device is already in Firmware Update Mode',upres,re.I):
                self.log_save(msg=upres)
            self.check_Yafuflash()

        if act == 'down':
            self.log_save(msg="Start down MLB cpld")
            cmd = '%s/Update.sh -kcs -cs 0x81 -nr -fb -d 4 %s' % (self.updatash,self.downfile)
            self.log_save(msg=cmd)
            os.chdir(self.updatash)
            print("Start down MLB cpld")
            downres = subprocess.getstatusoutput('%s/Update.sh -kcs -cs 0x81 -nr -fb -d 4 %s' % (self.updatash,self.downfile))[1]
            if re.search(r'Device is already in Firmware Update Mode',downres,re.I):
                self.log_save(msg=downres)
            self.check_Yafuflash()

    def runcpld(self):
        self.system_log_act(act='clear')
        for c in range(1,int(self.cyclecount)+1):
            count = "##########Test updata cpld cycle count :%s##########" % c
            print("##########Test updata cpld cycle count :%s##########" % c)
            self.log_save(msg=count)
            if self.sxflag:
                beforever = self.cpld_check(check='before')
                self.cpld_action(act='up')
                time.sleep(5)
                afterver = self.cpld_check(check='after')
                if beforever == afterver:
                    self.log_save(msg="##########Updata cpld fail##########")
                    sys.exit("updata cpld fail log save in %s" % self.logpath)
                else:
                    time.sleep(60)
                    beforever = self.cpld_check(check='before')
                    self.cpld_action(act='down')
                    time.sleep(5)
                    afterver = self.cpld_check(check='after')
                    if beforever == afterver:
                        self.log_save(msg="##########Updata cpld fail##########")
                        sys.exit("updata cpld fail log save in %s" % self.logpath)
                    else:
                        self.log_save(msg="##########Updata cpld sucess##########")
                        self.log_save()
            else:
                beforever = self.cpld_check(check='before')
                self.cpld_action(act='down')
                time.sleep(5)
                afterver = self.cpld_check(check='after')
                if beforever == afterver:
                    self.log_save(msg="##########Updata cpld fail##########")
                    sys.exit("updata cpld fail log save in %s" % self.logpath)
                else:
                    time.sleep(60)
                    beforever = self.cpld_check(check='before')
                    self.cpld_action(act='up')
                    time.sleep(5)
                    afterver = self.cpld_check(check='after')
                    if beforever == afterver:
                        self.log_save(msg="##########Updata cpld fail##########")
                        sys.exit("updata cpld fail log save in %s" % self.logpath)
                    else:
                        self.log_save(msg="##########Updata cpld sucess##########")
                        self.log_save()
        self.system_log_act(act='save')
        self.log_save(msg="Test cpld cycle over log save in %s" % self.logpath)
        self.log_save(msg="system log save in please check  %s" % self.log_filter_path)
        print("Test cpld cycle over log save in %s" % self.logpath)
        print("system log save in please check  %s" % self.log_filter_path)

if __name__ == '__main__':
    pars = argparse.ArgumentParser()
    pars.description='please input the parameter EX :python3 cpld_cycle.py -n 5 -t /root/Palos-H-ABS-V011400 -u /root/Update/palos_MLB_CPLD_v08_0xB0CB.jed -d /root/down/palos_MLB_CPLD_v07_0x9C9F.jed'
    pars.add_argument('-n','--cycle_count',required=False,default='5',help='please input NIC FW updata counts')
    pars.add_argument('-t','--updatetoolpath',required=True,help="please input the path of Update.sh ex /root/Palos-H-ABS-V011400")
    pars.add_argument('-u','--updata_file',required=True,help='please input the NIC up cpld file ex /root/down/palos_MLB_CPLD_v07_0x9C9F.jed')
    pars.add_argument('-d','--down_file',required=True,help='please input the down up cpld file ex ')
    argspart = vars(pars.parse_args())
    if re.search(r'v\d+',argspart['updata_file'],re.I):
        upfilever = re.search(r'v\d+',argspart['updata_file'],re.I).group(0).split('v')[1]
    else:
        upfilever = input("Not find up version in %s please input ex : 08..\n" % argspart['updata_file'])
    if re.search(r'v\d+',argspart['down_file'],re.I):
        downfilever = re.search(r'v\d+',argspart['down_file'],re.I).group(0).split('v')[1]
    else:
        downfilever = input("Not find down version in %s please input ex : 07..\n" % argspart['down_file'])
    cpldobj = Cpld_Cycle(count=argspart['cycle_count'],updatash=argspart['updatetoolpath'],updatafile=argspart['updata_file'],upver=upfilever,downfile=argspart['down_file'],downver=downfilever)
    cpldobj.runcpld()
