import os
import re
import sys
import copy
import json
import subprocess
import threading
import argparse

tea_path = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.pardir,
        os.pardir
        )
)
sys.path.append(tea_path)
from common.other.log import Logger

if re.search(r'%s' % os.path.abspath('.'), os.path.dirname(__file__), re.I):
    baselocallogpath = os.path.dirname(__file__)
else:
    if os.path.dirname(__file__).split('/')[0] != '':
        baselocallogpath = os.path.abspath('.') + "/" + os.path.dirname(__file__)
    else:
        baselocallogpath = os.path.abspath('.') + os.path.dirname(__file__)
scriptdir = baselocallogpath
baselocallogpath = baselocallogpath + '/' + 'result/fw_updata/'

class Fw_Updata():
    '''
    author :wanglei
    description :class init ,init fw_cycle count checkip up nic_fw file down nic_fw file,
    params :count;checkip;upfwfile;downfwfile
            {
                count: 'xxx'
                checkip: 'xxx'
                upfwfile: 'xxx'
                    .
                    .
                    .
            }
    '''
    def __init__(self,**kwargs):
        self.nicdev = ''
        self.nicname = []
        self.nic_device_port = []
        self.nicbusid = ''
        self.nic_port_info = {}
        self.count = kwargs.get('count','0')
        self.checkip = kwargs.get('checkip')
        self.upfwfile = kwargs.get('upfwfile')
        self.upfwversion = kwargs.get('upfwver')
        self.downfwfile = kwargs.get('downfwfile')
        self.downfwversion = kwargs.get('downfwver')
        self.nicport = kwargs.get('nicport')
        self.nictype = kwargs.get('nictype')
        self.withio = kwargs.get('withio')
        for nictmp in self.nicport.split(" "):
            bustmp = subprocess.getstatusoutput("ethtool -i %s |grep -i '^bus-info'| awk -F ' ' '{print $NF}'" % nictmp)[1].strip()
            self.nic_port_info[nictmp] = bustmp
        self.savepath = scriptdir.split('standalone')[0] + "standalone/network/result/fw_updata/"
        self.log_filter_path = scriptdir.split('standalone')[0] + 'standalone/common_test/log-parser/'

        if int(self.count) != 0:
            os.system('rm -rf %s/*' % baselocallogpath)
            self.clear_cmd()
            self.log_handle(act='clear')
        self.setupfile = baselocallogpath + "fw_info.txt"
        self.runlogfile = baselocallogpath + "run_test.log"
        self.fwchecklog = baselocallogpath + "fwcheck.log"
        self.pciedir = baselocallogpath + "pciedir"
        if not os.path.isdir(self.pciedir):
            os.makedirs(self.pciedir)
        self.nicfwlogger = Logger(log_file=self.runlogfile,log_file_timestamp=False,stdoutput=False)

    def log_handle(self,act):
        if act == 'clear':
            os.system('python3 %slog_parser.py --b' % self.log_filter_path)
        elif act == 'save':
            os.system('python3 %slog_parser.py --a' % self.log_filter_path)
            os.system('cp -r %sreports %s' % (self.log_filter_path,self.savepath))

    def clear_cmd(self):
        '''
        author :wanglei
        description :clean /etc/rc.d/rc.local
        params :none
        '''
        os.system("sed -i '/nic_fw_updata.py/d' /etc/rc.d/rc.local")

    def check_command(self,cmdlist):
        '''
        author :wanglei
        description :check mst flint ethtool command if exist
        params :none
        '''
        cmdflag = True
        checklist = cmdlist
        for cmd in checklist:
            res = subprocess.getstatusoutput(cmd)[1]
            if re.search(r'command not found',res,re.I):
                self.nicfwlogger.error("command not find : %s" % cmd)
                cmdflag = False
        return cmdflag

    def init_nic_dev_broadcom(self):
        '''
        author :wanglei
        description :init env mst start and get nicname(enp..) nicbusid(0000:02:09.0) nicdev(/dev/mst/mt4117_pciconf0)
        params :none
        '''
        if not self.check_command(cmdlist=['bnxtnvm','ethtool']):
            self.clear_cmd()
            sys.exit("FW updata command not find please check log %s" % self.runlogfile)
        else:
            device_in = subprocess.getstatusoutput('bnxtnvm device_info |grep -i "Device Interface Name" |tail -n1')[1]
            if device_in == "":
                self.nicfwlogger.error(f"Not Find Device Interface Name Use Command bnxtnvm device_info")
                self.clear_cmd()
                sys.exit(f"Not Find Device Interface Name Use Command bnxtnvm device_info")
            else:
                self.nicdev = device_in.split(":")[-1].strip()
                print(f"Find bnxtnvm device {self.nicdev}")

    def init_nic_dev(self):
        '''
        author :zonghuo liu
        description :init env mst start and get nicname(enp..) nicbusid(0000:02:09.0) nicdev(/dev/mst/mt4117_pciconf0)
        params :none
        '''
        businfo_list = subprocess.getstatusoutput("lspci |grep -i ' Ethernet controller'| awk -F ' ' '{print $1F}'")[1].split("\n")
        for businfo in businfo_list:
            nic_devices = subprocess.getstatusoutput("ls -l /sys/class/net/ | grep %s |awk -F ' ' '{print $9F}'"% businfo)[1].split("\n")
            self.nic_device_port.append(nic_devices)
        nic_driver_load_list = ['sssudk','sssdk','sssnic']
        for nic_driver_load in nic_driver_load_list:
            subprocess.getstatusoutput("modprobe %s"% nic_driver_load)
        # print(nic_device_port)
   
    def first_setup(self):
        '''
        author :wanglei
        description :first run need create info file,total_count: total run count current_count: current run count failfulsh_count: fail count if > 3 test fail ServerNic_hw_count: lspci get hw port count
        params :none
                {
                    total_count: 'xxx'
                    current_count: 'xxx'
                    failfulsh_count: 'xxx'
                    ServerNic_hw_count: 'xxx'
                }
        '''
        fw_info_dict = {}
        serverhwcount = subprocess.getstatusoutput("lspci | grep -i eth | wc -l")[1]
        fw_info_dict['total_count'] = self.count
        fw_info_dict['current_count'] = 0
        fw_info_dict['failfulsh_count'] = 0
        fw_info_dict['ServerNic_hw_count'] = serverhwcount
        nic_port_id = {}
        for porttmp in self.nicport.split(" "):
            nic_port_id[porttmp] = self.vid_sid_get(checkport=porttmp)
        fw_info_dict['nic_port_deviceid'] = nic_port_id
        with open(self.setupfile,'w') as f:
            f.write(str(fw_info_dict))
        for k,v in self.nic_port_info.items():
            pcieinfo = subprocess.getstatusoutput('lspci -s %s -vvv |grep -iE "LnkCap:|LnkSta:"' % v)[1]
            with open("%s/old_pcie.txt" % self.pciedir,"a") as f:
                f.write("%s\n" % k)
                f.write("%s\n" % pcieinfo)
        os.system("chmod -R 777 /etc/rc.d/rc.local")
        cyclecmd = 'cd %s && python3 nic_fw_updown.py -t %s -w %s -i %s -p "%s" -u %s -d %s' % (scriptdir,self.nictype,self.withio,self.checkip,self.nicport,self.upfwfile,self.downfwfile)
        with open("/etc/rc.d/rc.local", "a") as f :
            f.write("%s\n" % cyclecmd)

    def get_count(self):
        '''
        author :wanglei
        description :get count from info file if file not find return testcount = 0 else testcount = info.get('current_count')
        params :none
        '''
        gettmp = subprocess.getstatusoutput('cat %s/fw_info.txt' % baselocallogpath)[1]
        if re.search(r'No such file or directory',gettmp,re.I):
            testcount = 0
        else:
            with open(self.setupfile,'r') as f:
                info = eval(f.read())
            testcount = info.get('current_count')
        return testcount

    def ping_stress(self):
        subprocess.getstatusoutput("ping %s" % self.checkip)

    def vid_sid_get(self,checkport):
        vid_sid_dict = {}
        for nickey in ['vendor' ,'device', 'subsystem_vendor', 'subsystem_device']:
            vid_sid_dict[nickey] = subprocess.getstatusoutput('cat /sys/class/net/%s/device/%s' % (checkport,nickey))[1]
        return vid_sid_dict

    def Fw_Updata_Fun_broadcom(self,action):
        '''
        author :wanglei
        description :according to action decide up or down nic fw
        params :none
        '''
        if self.checkip != "None" and self.withio == "True":
            pingt = threading.Thread(target=self.ping_stress)
            pingt.start()
        if action == 'up':
            self.nicfwlogger.info(f"bnxtnvm -force -y -dev={self.nicdev} install {self.upfwfile}")
            print(f"bnxtnvm -force -y -dev={self.nicdev} install {self.upfwfile}")
            update_res = subprocess.getstatusoutput(f"bnxtnvm -force -y -dev={self.nicdev} install {self.upfwfile}")[1]
            self.nicfwlogger.info(update_res) 
        if action == 'down':
            self.nicfwlogger.info(f"bnxtnvm -force -y -dev={self.nicdev} install {self.downfwfile}")
            print(f"bnxtnvm -force -y -dev={self.nicdev} install {self.downfwfile}")
            update_res = subprocess.getstatusoutput(f"bnxtnvm -force -y -dev={self.nicdev} install {self.downfwfile}")[1]
            self.nicfwlogger.info(update_res)
        os.system('reboot')      

    def Fw_Updata_Fun(self,action):
        '''
        author : zonghuoliu
        description :according to action decide up or down nic fw
        params :none
        '''
        
        if self.checkip != "None" and self.withio == "True":
            pingt = threading.Thread(target=self.ping_stress)
            pingt.start()
        if action == 'up':
            self.nicfwlogger.info("sssnictool updatefw -i %s -f %s -a cold\n" % (self.nic_device_port[0],self.upfwfile))
            print("sssnictool updatefw -i %s -f %s -a cold\n" % (self.nic_device_port[0],self.upfwfile))
            update_res = subprocess.getstatusoutput("sssnictool updatefw -i %s -f %s -a cold" % (self.nic_device_port[0],self.upfwfile))[1]
            self.nicfwlogger.info(update_res)
        if action == 'down':
            self.nicfwlogger.info("sssnictool updatefw -i %s -f %s -a cold\n" % (self.nic_device_port[0],self.downfwfile))
            print("sssnictool updatefw -i %s -f %s -a cold\n" % (self.nic_device_port[0],self.downfwfile))
            update_res = subprocess.getstatusoutput("sssnictool updatefw -i %s -f %s -a cold" % (self.nic_device_port[0],self.downfwfile))[1]
            self.nicfwlogger.info(update_res)
        os.system('reboot')

    def Fw_Check_Fun(self,exceptfw,curcount):
        '''
        author :wanglei
        description :check fw version except fw if equal current version
        params :excpet fw ,current cycle count
        '''
        nicport = []
        for k in self.nic_port_info.keys():
            nicport.append(k)
        verport0 = subprocess.getstatusoutput("ethtool -i %s |grep -i '^firmware-version:'" % nicport[0])[1]
        verport1 = subprocess.getstatusoutput("ethtool -i %s |grep -i '^firmware-version:'" % nicport[1])[1]
        if verport0 == "" or verport1 == "":
            self.nicfwlogger.error("Get current fw version fail please check ethtool -i %s/%s" % (nicport[0],nicport[1]))
            self.clear_cmd()
            sys.exit()
        else:
            if verport0 == verport1:
                if re.search(r'\d+\.\d+\.\d+',verport0,re.I):
                    if argspart['nictype'] == 'Broadcom':
                        current_version = verport0.split("pkg")[-1].strip()
                    elif argspart['nictype'] == 'Nvidia' or argspart['nictype'] == 'Mlnx':
                        current_version = re.search(r'\d+\.\d+\.\d+',verport0,re.I).group(0).replace('.','_').strip()
                    print('current nic version: %s' % current_version)
                    print('expect nic version : %s' % exceptfw)
                    if current_version == exceptfw:
                        with open(self.fwchecklog,'a') as f:
                            f.write("**********Test count  :%s**********\n" % curcount)
                            f.write("Current_Nic_Version \n")
                            f.write("%s : %s\n" % (nicport[0],verport0))
                            f.write("%s : %s\n" % (nicport[1],verport1))
                            f.write("Exception_Nic_Version :%s\n" % exceptfw)
                            f.write("**********Test   Sucess  **********\n")
                            f.write("\n")
                        return True
                    else:
                        return False
            else:
                self.nicfwlogger.error("FW Check fail %s : %s %s : %s" % (nicport[0],verport0,nicport[1],verport1))
                self.clear_cmd()
                sys.exit()

    def ping_nin(self):
        '''
        author :wanglei
        description: this method is check server client net status
        return:
        if net status is ok return True else return False
        '''
        ping_count = 1
        while True:
            cmdout = subprocess.getstatusoutput(f"ping -c 3 {self.checkip}")[1]
            if re.search('100% packet loss', cmdout, re.I):
                self.nicfwlogger.warn(f"checkip :{self.checkip} is not available!")
                if ping_count > 3:
                    return False
            elif re.search(r'.*\s0% packet loss', cmdout, re.I):
                self.nicfwlogger.info(f"clientip :{self.checkip} is OK!")
                return True
            elif re.search(r'(.*\s[3-6][3-6]% packet loss)', cmdout, re.I):
                self.nicfwlogger.warn(f"checkip :{self.checkip} has networking issue. Please check it!")
                if ping_count > 3:
                    return False
            ping_count += 1

    def Check_Nic_State(self,initinfo,count):
        '''
        author :wanglei
        description :check lspci nic port if lack
        '''
        new_nic_portid = {}
        write_data = {}
        for porttmp in self.nicport.split(" "):
            new_nic_portid[porttmp] = self.vid_sid_get(checkport=porttmp)
        if new_nic_portid == initinfo.get('nic_port_deviceid'):
            self.nicfwlogger.info("check VID DID SVID SSID success")
            write_data["count num : %s" % count] = new_nic_portid
            with open('%s/nic_device_id.txt' % baselocallogpath,"a") as f:
                aj = json.dumps(write_data,indent=4)
                f.write(aj)
                f.write('\n')
        else:
            self.nicfwlogger.error("check device id fail")
            self.clear_cmd()
            sys.exit()

        for k,v in self.nic_port_info.items():
            pcieinfo = subprocess.getstatusoutput('lspci -s %s -vvv |grep -iE "LnkCap:|LnkSta:"' % v)[1]
            with open("%s/count%s_pcie.txt" % (self.pciedir,count),"a") as f:
                f.write("%s\n" % k)
                f.write("%s\n" % pcieinfo)
        oldinfo = subprocess.getstatusoutput('cat %s/old_pcie.txt' % self.pciedir)[1]
        newinfo = subprocess.getstatusoutput('cat %s/count%s_pcie.txt' % (self.pciedir,count))[1]
        if oldinfo == newinfo:
            self.nicfwlogger.info("Check LnkCap LnkSta success")
        else:
            self.nicfwlogger.error("Check LnkCap LnkSta error")
            self.clear_cmd()
            sys.exit("Check LnkCap LnkSta error")
        
        oldportnum = initinfo.get('ServerNic_hw_count')
        newportnum = subprocess.getstatusoutput("lspci | grep -i eth | wc -l")[1]
        if oldportnum != newportnum:
            self.nicfwlogger.error("check dut HW port num fail before test count %s after test count %s" % (oldportnum,newportnum))
            self.nicfwlogger.error(subprocess.getstatusoutput("lspci | grep -i eth | wc -l")[1])
            self.clear_cmd()
            sys.exit("check dut HW port num fail before test count %s after test count %s" % (oldportnum,newportnum))
        else:
            self.nicfwlogger.info("check dut HW port num success")
        if self.checkip != "None":
            if self.ping_nin() == False:
                self.clear_cmd()
                sys.exit("ping checkip %s fail please checklog %s" % (self.checkip,self.runlogfile))

    def run_cycle(self):
        fwcheckflag = True
        if self.nictype == 'Broadcom':
            self.init_nic_dev_broadcom()
        elif self.nictype == 'Nvidia' or self.nictype == 'Mlnx':
            self.init_nic_dev()
        cur_count = self.get_count()
        if cur_count == 0:
            fwcheckflag = False
            self.first_setup()
            cur_count = cur_count + 1
        else:
            cur_count = cur_count + 1
        with open(self.setupfile,'r') as f:
            info = eval(f.read())
        self.Check_Nic_State(initinfo=info,count=cur_count)
        if fwcheckflag:
            if self.Fw_Check_Fun(exceptfw=info.get('expect_nif_version'),curcount=info.get('current_count')):
                info['failfulsh_count'] = 0
                with open(self.setupfile,'w') as f:
                    f.write(str(info))
            else:
                failcount = info.get('failfulsh_count')
                if failcount > 2:
                    self.nicfwlogger.error('updata NIC fw version fail count more then 3 times fail updata %s' % info.get('expect_nif_version'))
                    self.log_handle(act='save')
                    self.clear_cmd()
                    sys.exit('updata NIC fw version fail count more then 3 times fail updata %s' % info.get('expect_nif_version'))
                else:
                    failcount = failcount + 1
                    info['failfulsh_count'] = failcount
                    with open(self.setupfile,'w') as f:
                        f.write(str(info))
                    self.nicfwlogger.warn('updata NIC fw version fail and try 3 times %s' % info.get('expect_nif_version'))
                    if info.get('expect_nif_version') == self.upfwversion:
                        if self.nictype == 'Broadcom':
                            self.Fw_Updata_Fun_broadcom(action='up')
                        elif self.nictype == 'Nvidia' or self.nictype == 'Mlnx':
                            self.Fw_Updata_Fun(action='up')
                    elif info.get('expect_nif_version') == self.downfwversion:
                        if self.nictype == 'Broadcom':
                            self.Fw_Updata_Fun_broadcom(action='down')
                        elif self.nictype == 'Nvidia' or self.nictype == 'Mlnx':
                            self.Fw_Updata_Fun(action='down')
        if int(cur_count) <= int(info.get('total_count')):
            if cur_count % 2 == 1:
                info['current_count'] = cur_count
                info['expect_nif_version'] = self.upfwversion
                with open(self.setupfile,'w') as f:
                    f.write(str(info))
                if self.nictype == 'Broadcom':
                    self.Fw_Updata_Fun_broadcom(action='up')
                elif self.nictype == 'Nvidia' or self.nictype == 'Mlnx':
                    self.Fw_Updata_Fun(action='up')
            elif cur_count % 2 == 0:
                info['current_count'] = cur_count
                info['expect_nif_version'] = self.downfwversion
                with open(self.setupfile,'w') as f:
                    f.write(str(info))
                if self.nictype == 'Broadcom':
                    self.Fw_Updata_Fun_broadcom(action='down')
                elif self.nictype == 'Nvidia' or self.nictype == 'Mlnx':
                    self.Fw_Updata_Fun(action='down')
        else:
            self.clear_cmd()
            self.log_handle(act='save')

if __name__ == '__main__':
    pars = argparse.ArgumentParser()
    pars.description='For Mlnx/Nvidia :python3 nic_fw_updata.py -i 192.168.2.2 -n 4 -t Nvidia -p "eth0 eth1" -u upfile.bin -d downfile.bin,\
                      For Broadcom    :python3 nic_fw_updata.py -i 192.168.2.2 -n 4 -t Broadcom -p "eth0 eth1" -u upfile.pkg -d downfile.pkg'

    pars.add_argument('-n','--cycle_count',required=False,default='0',help='please input NIC FW updata counts')
    pars.add_argument('-i','--check_ip',required=False,default="None",help='please input checkip')
    pars.add_argument('-p','--nicport',required=True,help='input need test port ex:-p "ethxx ethxx"')
    pars.add_argument('-t','--nictype',required=True,help='input nic card type Nvidia/Broadcom/Mlnx')
    pars.add_argument('-w','--withio',required=False,default="False",help='input if with io in updata action')
    pars.add_argument('-u','--updata_file',required=True,help='please input the NIC up FW file')
    pars.add_argument('-d','--down_file',required=True,help='please input the down up FW file')

    argspart = vars(pars.parse_args())
    if re.search(r'\d+_\d+_\d+',argspart['updata_file'],re.I) or re.search(r'\d+\.\d+\.\d+\.\d+',argspart['updata_file'],re.I):
        if argspart['nictype'] == 'Broadcom':
            upfw_version = re.search(r'\d+\.\d+\.\d+\.\d+',argspart['updata_file'],re.I).group(0)
        elif argspart['nictype'] == 'Nvidia' or argspart['nictype'] == 'Mlnx': 
            upfw_version = re.search(r'\d+_\d+_\d+',argspart['updata_file'],re.I).group(0)
    else:
        upfw_version = input("get up fw file version fail please input manal ex: 7_3_21\n")

    if re.search(r'\d+_\d+_\d+',argspart['down_file'],re.I) or re.search(r'\d+\.\d+\.\d+\.\d+',argspart['down_file'],re.I):
        if argspart['nictype'] == 'Broadcom':
            downfw_version = re.search(r'\d+\.\d+\.\d+\.\d+',argspart['down_file'],re.I).group(0)
        elif argspart['nictype'] == 'Nvidia' or argspart['nictype'] == 'Mlnx': 
            downfw_version = re.search(r'\d+_\d+_\d+',argspart['down_file'],re.I).group(0)
    else:
        downfw_version = input("get down fw file version fail please input manal ex: 7_3_20\n")
    
    fwobj = Fw_Updata(count=argspart['cycle_count'],\
                      checkip=argspart['check_ip'],\
                      upfwfile=argspart['updata_file'],\
                      upfwver=upfw_version,\
                      downfwfile=argspart['down_file'],\
                      downfwver=downfw_version,\
                      nicport=argspart['nicport'],nictype=argspart['nictype'],withio=argspart['withio'])
    fwobj.run_cycle()
