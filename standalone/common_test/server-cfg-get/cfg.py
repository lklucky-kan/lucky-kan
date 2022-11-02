import os
import re
import sys
import time
import copy
import fabric
import argparse
import threading
import subprocess
tea_path = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.pardir,
        os.pardir,
        os.pardir
        )
)
sys.path.append(tea_path)
from autotest.testLib.sit.nic_function import MyThread
from common.file.mondb import *
from common.file.json_rw import fopen


if re.search(r'%s' % os.path.abspath('.'),os.path.dirname(__file__),re.I):
    cfg_json_path = os.path.dirname(__file__) + "/cfg.json"
    dirpath = os.path.dirname(__file__)
else:
    cfg_json_path = os.path.abspath('.') + "/" + os.path.dirname(__file__) + "/cfg.json"
    dirpath = os.path.abspath('.') + "/" + os.path.dirname(__file__)

class MyThread(threading.Thread):
    '''
    author: wanglei
    description: this class use to create thread and get thread result
    params: func:thread function args:thread function args 
    use:
    MyThread(self.check_vlan,args=(serverssh,serport))
    '''
    def __init__(self, func, args=()):
        super(MyThread, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result
        except Exception:
            return None

        return None

class CfgGet():

    def __init__(self,name,mondb=False,csvlist=[],**kwargs):
        """
        author : wanglei
        description : class init method init object name , check if save data into mondb , if need add server info tmp into mondb
        """
        self.dutlist = []    
        self.objectname = name
        self.mondbflag = mondb
        self.csvlist = csvlist
        self.objectcfg = kwargs.get(self.objectname)
        for key in self.objectcfg.keys():
            if re.search(r'sku\d+',key,re.I):
                self.dutlist.append(key)
    
    def ping(self, ip):
        """
        author : wanglei
        description : check sku network available and try 3 times 
        return : if sku network available return True , else return False
        """
        ping_count = 0
        while True:
            ping_count += 1
            cmd_out = subprocess.getstatusoutput('ping -c 3 ' + ip)[1]     
            if re.search('100% packet loss', cmd_out, re.I):
                if ping_count > 3:
                    return False
                else:
                    continue
            elif re.search(r'.*\s0% packet loss', cmd_out, re.I):
                return True
            elif re.search(r'(.*\s[3-6][3-6]% packet loss)', cmd_out, re.I):
                if ping_count > 3:
                    return False
                else:
                    continue
            time.sleep(2)
          
    def cpuinfo(self,dutremote,filedes=None):
        """
        author : wanglei
        description : get cpu info,include cpu model name;cpu current hz;cpu max hz;cpu cores.
        return : cpuinfo_dict {
                                Model name : xxxx,
                                CPU curentMhz : xxxx,
                                CPU maxMhz : xxxx,
                                CPU_Core : xxxx
                              }
        """
        cpuinfo_dict = {}
        cpu_socketnum = dutremote.run('lscpu |grep -i "^Socket"',hide=True,warn=True).stdout.strip()
        cpu_modename = dutremote.run('lscpu |grep -i "^Model name"',hide=True,warn=True).stdout.strip()
        cpu_curmhz = dutremote.run('lscpu |grep -i "^CPU MHz"',hide=True,warn=True).stdout.strip()
        cpu_maxmhz = dutremote.run('lscpu |grep -i "^CPU max MHz:"',hide=True,warn=True).stdout.strip()
        cpu_core = dutremote.run('lscpu |grep -i "^Core(s) per socket"',hide=True,warn=True).stdout.strip()
        cpuinfo_dict['CPU socket counts'] = str(cpu_socketnum).split(":")[-1].strip()
        cpuinfo_dict['CPU model name'] = str(cpu_modename).split(":")[-1].strip()
        cpuinfo_dict['CPU curentMhz'] = str(cpu_curmhz).split(":")[-1].strip()
        cpuinfo_dict['CPU maxMhz'] = str(cpu_maxmhz).split(":")[-1].strip()
        cpuinfo_dict['CPU_Core'] = str(cpu_core).split(":")[-1].strip()
        if filedes:
            filedes.write("CPU Socket Counts,CPU Model Name,CPU CurentMhz,CPU MaxMhz,CPU_Core\n")
            cpuinfo = str(cpu_socketnum).split(":")[-1].strip() + "," + str(cpu_modename).split(":")[-1].strip() + "," + str(cpu_curmhz).split(":")[-1].strip() + "," + str(cpu_maxmhz).split(":")[-1].strip() + "," + str(cpu_core).split(":")[-1].strip() + "\n"
            filedes.write(cpuinfo)
            filedes.write("\n")
        return cpuinfo_dict

    def memoryinfo(self,dutremote,filedes=None):
        """
        author : wanglei
        description : get memory info,include Memory Manufacturer;Memory Partnumber;Memory Speed;Mem_Size;Mem_Counts
        return : memoryinfo_dict {
                                Memory Manufacturer : xxxx,
                                Memory Partnumber : xxxx,
                                Memory Speed : xxxx,
                                Mem_Size : xxxx,
                                Mem_Counts : xxxx
                              }
        """
        memoryinfo_dict = {}
        mem_manufacturer = dutremote.run('dmidecode -t memory |sed s/^[[:space:]]//g |grep -i "Manufacturer:" |grep -ivE "Unknown|NO DIMM" |uniq',hide=True,warn=True).stdout.strip()
        mem_partnumber = dutremote.run("dmidecode -t memory |grep -i 'Part Number' |grep -ivE 'Unknown|NO DIMM' |uniq |awk -F ':' '{print $2}'",hide=True,warn=True).stdout.strip()
        mem_cfgspeed = dutremote.run('dmidecode -t memory |sed s/^[[:space:]]//g |grep -i "^Speed"|grep -iv "Unknown"|uniq',hide=True,warn=True).stdout.strip()
        mem_size = dutremote.run('dmidecode |sed s/^[[:space:]]//g |grep -i "^Size:" |egrep -iv "None|Installed|Volatile" |uniq',hide=True,warn=True).stdout.strip()
        mem_count = dutremote.run('dmidecode |sed s/^[[:space:]]//g |grep -i "^Size:" |egrep -iv "None|Installed|Volatile" |wc -l',hide=True,warn=True).stdout.strip()
        mem_locator = dutremote.run("dmidecode -t memory |sed s/^[[:space:]]//g |grep -i '^Locator:' |awk -F ':' '{print $NF}'",hide=True,warn=True).stdout.strip()
        if mem_locator:
            mem_locator = mem_locator.split("\n")
        else:
            mem_locator = 'Not check'
        memoryinfo_dict['Memory Manufacturer'] = str(mem_manufacturer).split(":")[-1].strip()
        memoryinfo_dict['Memory Partnumber'] = str(mem_partnumber)
        memoryinfo_dict['Memory Speed'] = str(mem_cfgspeed).split(":")[-1].strip()
        memoryinfo_dict['Mem_Size'] = str(mem_size).split(":")[-1].strip()
        memoryinfo_dict['Mem_Counts'] = str(mem_count)
        memoryinfo_dict['Mem_Locator'] = ",".join(mem_locator)
        if filedes:
            filedes.write("Memory Manufacturer,Memory Partnumber,Memory Speed,Mem_Size,Mem_Counts\n")
            meminfo = str(mem_manufacturer).split(":")[-1].strip() + "," + str(mem_partnumber) + "," + str(mem_cfgspeed).split(":")[-1].strip() + "," + str(mem_size).split(":")[-1].strip() + "," + str(mem_count) + "\n"
            filedes.write(meminfo)
            filedes.write("Mem_Locator\n")
            filedes.write(str(memoryinfo_dict['Mem_Locator']))
            filedes.write("\n")
            filedes.write("\n")
        return memoryinfo_dict

    def fwinfo(self,dutremote,dutname,filedes=None):
        """
        author : wanglei
        description : get fw info,include BMC_fw;BIOS_fw
        return : fwinfo_dict {
                                BMC_fw : xxxx,
                                BIOS_fw : xxxx
                              }
        """       
        cpldinfodict = {}
        fwinfo_dict = {}
        bmc_fwinfo = dutremote.run('ipmitool mc info |grep -i "^Firmware Revision"',hide=True,warn=True).stdout.strip()
        bios_fwinfo = dutremote.run('dmidecode -t bios |sed s/^[[:space:]]//g |grep -i "^Version:"',hide=True,warn=True).stdout.strip()
       
        fwtitle = "BMC_fw" + "," + "BIOS_fw"
        fwinfo = str(bmc_fwinfo).split(":")[-1].strip() + "," + str(bios_fwinfo).split(":")[-1].strip()
        if self.objectcfg.get(dutname).get('cpldcmd'):
            for cpldkey,cpldvalue in self.objectcfg.get(dutname).get('cpldcmd').items():
                fwtitle = fwtitle + "," + str(cpldkey)
                cpldtmp = dutremote.run(cpldvalue,hide=True,warn=True).stdout.strip().split('\n')
                fwinfo = fwinfo + "," + "".join(cpldtmp)
                cpldinfodict[cpldkey] = "".join(cpldtmp)
        fwinfo_dict['BMC_fw'] = str(bmc_fwinfo).split(":")[-1].strip()
        fwinfo_dict['BIOS_fw'] = str(bios_fwinfo).split(":")[-1].strip()
        if filedes:
            fwtitle = fwtitle + "\n"
            filedes.write(fwtitle)
            fwinfo = fwinfo + "\n"
            filedes.write(fwinfo)
            filedes.write("\n")
        return fwinfo_dict

    def osinfo(self,dutremote,dutname,filedes=None):
        """
        author : wanglei
        description : get os info,include OS_Version;OS_Kernel_Version;OS_IP;BMC_IP
        return : osinfo_dict {
                                OS_Version : xxxx,
                                OS_Kernel_Version : xxxx,
                                OS_IP : xxxx,
                                BMC_IP : xxxx
                              }
        """
        osinfo_dict = {}
        os_info_title = "OS_Version" + "," + "OS_Kernel_Version" + "," + "OS_IP" + "," + "BMC_IP" + "," + "\n"
        bmc_ip = dutremote.run('ipmitool lan print 1 |grep -i "IP Address" |grep -iv "Source"',hide=True,warn=True).stdout.strip()
        if bmc_ip == "":
            bmc_ip = "Not Find"
        os_version = dutremote.run('cat /etc/redhat-release',hide=True,warn=True).stderr.strip()
        kernel_info = dutremote.run('uname -r',hide=True,warn=True).stdout.strip()
        if re.search(r'No such file or directory',os_version,re.I):
            os_version_tmp = dutremote.run('cat /etc/os-release |grep -i "PRETTY_NAME"',hide=True,warn=True).stdout.strip()
            os_version = os_version_tmp.split('=')[-1].split('"')[1].strip()
        else:
            os_version = dutremote.run('cat /etc/redhat-release',hide=True,warn=True).stdout.strip()
        os_info = os_version + "," + kernel_info + "," + self.objectcfg.get(dutname).get('osip') + "," + str(bmc_ip).split(":")[-1].strip() + "\n"
        osinfo_dict['OS_Version'] = os_version
        osinfo_dict['OS_Kernel_Version'] = kernel_info
        osinfo_dict['OS_IP'] = self.objectcfg.get(dutname).get('osip')
        osinfo_dict['BMC_IP'] = str(bmc_ip).split(":")[-1].strip()
        if filedes:
            filedes.write(os_info_title)
            filedes.write(os_info)
            filedes.write("\n")
        return osinfo_dict

    def nicinfo(self,dutremote,filedes=None):
        """
        author : wanglei
        description : get nic info,include Nic Manufacturer;Nic Speed;Nic Driver;Nic FW Version
        return : nicinfo_dict {
                                Nic Manufacturer : xxxx,
                                Nic Speed : xxxx,
                                Nic Driver : xxxx,
                                Nic FW Version : xxxx
                              }
        """
        nicinfo_dict = {}
        nicname = []
        savename = []
        netbusid = dutremote.run("lspci |grep -i 'Ethernet' |awk '{print$1}'",hide=True,warn=True).stdout.strip()
        if netbusid:
            for bustmp in netbusid.split("\n"):
                netbus = {}
                netnametmp = dutremote.run('ls /sys/bus/pci/devices/0000\:%s\:%s/net/' % (bustmp.split(":")[0],bustmp.split(":")[1]),hide=True,warn=True).stdout.strip()
                netbus[netnametmp] = bustmp
                nicname.append(copy.deepcopy(netbus))
                netbus.clear()
            for namet1 in copy.deepcopy(nicname):
                if nicname.index(namet1) % 2 == 0:
                    savename.append(namet1)
            for namet2 in savename:
                namet2['nic manufacturer'] = dutremote.run("lspci -s %s |awk -F 'controller' '{print $2}'|awk -F ' ' '{print $2}'" % [i for i in namet2.values()][0] ,hide=True, warn=True).stdout.strip()               
                namet2['nic speed'] = dutremote.run("ethtool %s |grep -i 'Speed'|awk -F ':' '{print $2}'" % [i for i in namet2.keys()][0], hide=True ,warn=True).stdout.strip()
                namet2['nic driver'] = dutremote.run("ethtool -i %s |grep -i 'driver' |awk -F ':' '{print $2}'" % [i for i in namet2.keys()][0], hide=True ,warn=True).stdout.strip()
                fwversion = dutremote.run("ethtool -i %s |grep -i 'firmware' |awk -F ':' '{print $2}'" % [i for i in namet2.keys()][0], hide=True ,warn=True).stdout.strip()
                if fwversion: 
                    namet2['nic FW version'] = fwversion
                else:
                    namet2['nic FW version'] = 'Not Find'
            nic_title = "Nic Counts"
            nic_info = str(len(savename))
            for infotmp in savename:
                nic_tmpdict = {}
                netkey = "Nic" + str(savename.index(infotmp))
                nic_title = nic_title + "," + "Nic Manufacturer" + "," + "Nic Speed" + "," + "Nic Driver" + "," + "Nic FW Version"
                nic_info = nic_info + "," + infotmp.get('nic manufacturer') + "," + infotmp.get('nic speed') + "," + infotmp.get('nic driver') + "," + infotmp.get('nic FW version')
                nic_tmpdict['Nic Manufacturer'] = infotmp.get('nic manufacturer')
                nic_tmpdict['Nic Speed'] = infotmp.get('nic speed')
                nic_tmpdict['Nic Driver'] = infotmp.get('nic driver')
                nic_tmpdict['Nic FW Version'] = infotmp.get('nic FW version')
                nicinfo_dict[netkey] = copy.deepcopy(nic_tmpdict)
                nic_tmpdict.clear()
            nic_title += "\n"
            nic_info += "\n"
            filedes.write(nic_title)
            filedes.write(nic_info)
            filedes.write("\n")
        return nicinfo_dict

    def diskinfo(self,dutremote,filedes=None):
        """
        author : wanglei
        description : get nic info,include Name Space;Device Model;Serial Number;Capacity;Firmware Version
        return : diskinfo_dict {
                                Name Space : xxxx,
                                Device Model : xxxx,
                                Serial Number : xxxx,
                                Capacity : xxxx,
                                Firmware Version : xxxx
                              }
        """
        diskinfo_dict = {}
        disklisttmp = dutremote.run("lsblk |grep -i disk |awk '{print $1}'",hide=True,warn=True).stdout.strip()
        if disklisttmp:
            diskinfodict = {}
            disklist = disklisttmp.split("\n")
            for diskns in disklist:
                tmpdict = {}
                if 'nvme' in diskns:
                    tmpdict['Device model'] = dutremote.run("nvme list |grep -i '/dev/%s' |awk '{print $3}'" % diskns ,hide=True, warn=True).stdout.strip()
                    tmpdict['Serial Number'] = "SN:" + str(dutremote.run("nvme list |grep -i '/dev/%s' |awk '{print $2}'" % diskns ,hide=True, warn=True).stdout.strip())
                    tmpdict['Capacity'] = dutremote.run("nvme list |grep -i '/dev/%s' |awk '{print $5 $6}'" % diskns ,hide=True, warn=True).stdout.strip()
                    tmpdict['Firmware Version'] = str(dutremote.run("nvme list |grep -i '/dev/%s' |awk '{print $NF}'" % diskns ,hide=True, warn=True).stdout.strip())
                else:
                    dmtmp = dutremote.run("smartctl -a /dev/%s |grep -i 'Device Model'" % diskns ,hide=True, warn=True).stdout.strip()
                    if dmtmp:
                        tmpdict['Device model'] = dmtmp.split(":")[-1].strip()
                    else:
                        tmpdict['Device model'] = dutremote.run("smartctl -a /dev/%s |grep -i 'Product'" % diskns ,hide=True, warn=True).stdout.strip().split(":")[-1].strip()
                    tmpdict['Serial Number'] = "SN:" + dutremote.run("smartctl -a /dev/%s |grep -i 'Serial Number'" % diskns ,hide=True, warn=True).stdout.strip().split(":")[-1].strip()
                    captmp = dutremote.run("smartctl -a /dev/%s |grep -i 'User Capacity'" % diskns ,hide=True, warn=True).stdout.strip().split(":")[-1].strip()
                    if captmp:
                        tmpdict['Capacity'] = re.search(r'\[.*\]',captmp,re.I).group(0).split("[")[1].split("]")[0]
                    else:
                        tmpdict['Capacity'] = "No Capacity"
                    tmpdict['Firmware Version'] = dutremote.run("smartctl -a /dev/%s |grep -i 'Firmware Version' |awk -F ':' '{print $2}'" % diskns ,hide=True ,warn=True).stdout.strip()
                diskinfodict[diskns] = copy.deepcopy(tmpdict)
                tmpdict.clear()
            for diskname in disklist:
                disktmp_dict = {}
                disk_title = "Name Space" + "," + "Device Model" + "," + "Serial Number" + "," + "Capacity" + "," + "Firmware Version" + "\n"
                disk_info = diskname + "," + diskinfodict.get(diskname).get('Device model') + "," + diskinfodict.get(diskname).get('Serial Number') + "," + diskinfodict.get(diskname).get('Capacity') + "," + diskinfodict.get(diskname).get('Firmware Version') + "\n"
                filedes.write(disk_title)
                filedes.write(disk_info)
                diskkey = 'Disk' + str(disklist.index(diskname))
                disktmp_dict['Name Space'] = diskname
                disktmp_dict['Device Model'] = diskinfodict.get(diskname).get('Device model')
                disktmp_dict['Serial Number'] = diskinfodict.get(diskname).get('Serial Number')
                disktmp_dict['Capacity'] = diskinfodict.get(diskname).get('Capacity')
                disktmp_dict['Firmware Version'] = diskinfodict.get(diskname).get('Firmware Version')
                diskinfo_dict[diskkey] = copy.deepcopy(disktmp_dict)
                disktmp_dict.clear()
        return diskinfo_dict

    def fur_check(self,dutremote,filedes=None):
        fru_dict = {}
        filedes.write('\n')
        chassis_type = dutremote.run('ipmitool fru',hide=True,warn=True).stdout.strip().split('\n')
        for fru_info in chassis_type[1:]:
            if fru_info != "":
                fru_dict[fru_info.split(':')[0].strip()] = fru_info.split(':')[1].strip()
                linetmp = fru_info.split(':')[0].strip() + "," + fru_info.split(':')[1].strip()
                filedes.write(linetmp)
                filedes.write('\n')
            else:
                break
        return fru_dict

    def getcfg(self,dutnametmp):
        """
        author : wanglei
        description : save server info into csv and if mondbflag=True save data into mondb
        """
        if self.ping(self.objectcfg.get(dutnametmp).get('osip')):
            mondbinfo = {}
            conn = fabric.Connection(self.objectcfg.get(dutnametmp).get('osip'),user=self.objectcfg.get(dutnametmp).get('username'),connect_kwargs={"password": self.objectcfg.get(dutnametmp).get('password')})
            cfgf = open("%s/%s-%s-%s-%s.csv" % (dirpath,self.objectname,self.objectcfg.get('stage'),'SIT',dutnametmp),'w') 
            mondbinfo['os_info'] = self.osinfo(conn,dutnametmp,cfgf)
            mondbinfo['fw_info'] = self.fwinfo(conn,dutnametmp,cfgf)
            mondbinfo['cpu_info'] = self.cpuinfo(conn,cfgf)
            mondbinfo['memory_info'] = self.memoryinfo(conn,cfgf)
            mondbinfo['nic_info'] = self.nicinfo(conn,cfgf)
            mondbinfo['disk_info'] = self.diskinfo(conn,cfgf)
            mondbinfo['fru_info'] = self.fur_check(conn,cfgf)
            conn.close()
            cfgf.close()
            with open("%s/%s-%s-%s-%s-info.txt" % (dirpath,self.objectname,self.objectcfg.get('stage'),'SIT',dutnametmp),'w') as f:
                f.write(str(mondbinfo))
            if self.mondbflag:
                id = "%s-%s-%s-%s-%s" % (self.objectname,self.objectcfg.get('stage'),'SIT',dutnametmp,time.strftime("%Y-%m-%d %A %X", time.localtime(time.time())))
                monobj = MongoDB()
                monobj.add_one_data(dataname=id,**mondbinfo)    
        else:
            print("please check sku ip if connection :%s" % self.objectcfg.get(dutnametmp).get('osip'))
        
    def save_data_into_mondb(self):
        monobj = MongoDB()
        print(self.csvlist)
        for datafilename in self.csvlist:
            mondata = {}
            with open(datafilename,'r') as f:
                mondata = eval(f.read())
                id = "%s-%s-%s-%s-%s" % (self.objectname,self.objectcfg.get('stage'),'SIT',re.search(r'sku\d+',datafilename,re.I).group(0),time.strftime("%Y-%m-%d %A %X", time.localtime(time.time())))
                monobj.add_one_data(dataname=id,**mondata)
            
    def run(self):
        threadlist = []
        for dut in self.dutlist:
            threadlist.append(MyThread(self.getcfg,args=(dut,)))
        for thread in threadlist:
            thread.start()
            thread.join() 

if __name__ == '__main__':
    pars = argparse.ArgumentParser()
    pars.add_argument("-p", "--name",required=False,default='none',help="please input object name")
    pars.add_argument("-m", "--mondb",required=False,default=False,help="if want to save to mondb -m True")
    pars.add_argument("-s", "--addsshag",required=False,default=False)
    pars.add_argument("-f", "--csvfile",required=False,default='none',help='input csv file which one save in mondb ex : "palos-EVT-SIT-sku1-info.txt:palos-EVT-SIT-sku2-info.txt"')
    argspart = vars(pars.parse_args())
    csvnamelist = []
    data = fopen(file=cfg_json_path,json=True)
    if argspart["csvfile"] != 'none':
        csvnamelist = argspart["csvfile"].split(":")
        cfgobj = CfgGet(name=argspart["name"],mondb=argspart["mondb"],csvlist=csvnamelist,**data)
        cfgobj.save_data_into_mondb()
    else:
        if argspart['addsshag']:
           sshagentmp = subprocess.getstatusoutput("ssh-agent |head -n2")[1].split("\n")
           os.system("sed -i '/SSH_AUTH_SOCK/d' /etc/profile")
           os.system("sed -i '/SSH_AGENT_PID/d' /etc/profile")
           os.system("sed -i '/Agent/d' /etc/profile")
           for cmd in sshagentmp:
               print(cmd.split(";")[0])
               command = 'export ' + cmd.split(";")[0]
               subprocess.getstatusoutput("echo %s >>/etc/profile" % command)
           subprocess.getstatusoutput("source /etc/profile") 
        cfgobj = CfgGet(name=argspart["name"],mondb=argspart["mondb"],**data)
        cfgobj.run()

    #m = MongoDB()
    #print(m.find_all(onlyid=True))
    
