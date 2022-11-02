import argparse
import os
import subprocess
import re
import sys
tea_path = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.pardir,
        os.pardir
        )
)
sys.path.append(tea_path)
from common.other.log import Logger  

pars = argparse.ArgumentParser()
pars.description='please input the parameter EX :python3 standalone/network/nic_bond_function.py -n "eth0 eth1" -b bondX -i bondip'
pars.add_argument("-n", "--netportname", required=False, help="please input netportname for bond example: 'eth0 eth1'")
pars.add_argument("-b", "--bondnum", required=False,default="bond0",help="please input bondnum example: bond0")
pars.add_argument("-i", "--bondip", required=False,default="192.168.10.10",help="please input bondip example: 192.168.10.10")
pars.add_argument("-r", "--recover",required=False,default="False",help="recover the network env")
pars.add_argument("-p", "--network_cfg_path", default="/etc/sysconfig/network-scripts", help="please input network cfg path default:/etc/sysconfig/network-scripts")
argspart = vars(pars.parse_args())

if re.search(r'%s' % os.path.abspath('.'), os.path.dirname(__file__), re.I):
    baselocallogpath = os.path.dirname(__file__) + "/result/bondlog/"
else:
    baselocallogpath = os.path.abspath('.') + "/" + os.path.dirname(__file__) + "/result/bondlog/"

class Bond_net():
    '''
    description: this class use to create bond object 
    author: wanglei
    params: eth:netportname bondnum:bond0 bond1.... bondip:default(192.168.10.10),netcfgpath:/etc/sysconfig/network-scripts
    '''
    def __init__(self,args):
        self.eth = args["netportname"].split(" ")
        self.bondnum = args["bondnum"]
        self.bondip = args["bondip"]
        self.netcfgpath = args["network_cfg_path"]
        self.eth0,self.eth1 = args["netportname"].split(" ")
        self.portstate = {self.bondnum:True, self.eth0:True, self.eth1:True}

    def clear_bond(self):
        '''
        description: this method is clean bond env
        '''
        bondport = subprocess.getstatusoutput("ifconfig |grep -i bond |awk '{print $1}'")[1]
        if bondport != "":
            bondport = bondport.split("\n")
            for porttmp in bondport:
                os.system("ifconfig %s down >/dev/zero 2>&1" % porttmp.split(":")[0])
                os.system("ifdown %s >/dev/zero 2>&1" % porttmp.split(":")[0])

        for root, dirs, files in os.walk(self.netcfgpath):
            for bondfile in files:
                if re.search(r'bond', bondfile, re.I):
                    os.system("rm -rf %s/%s" % (self.netcfgpath,bondfile))

        for root, dirs, files in os.walk("/etc/modprobe.d/"):
            for bondfile in files:
                if re.search(r'bond.+', bondfile, re.I):
                    os.system("rm -rf /etc/modprobe.d/%s" % bondfile)

    def create_ifcfg_file(self):
        '''
        description: this method is create/modify /etc/sysconfig/network-scripts/ifcfg-xx 
        '''
        for ethport in self.eth:
            logger.info("create/modify ifcfg-%s" % ethport)
            with open("%s/ifcfg-%s" % (self.netcfgpath,ethport), "w") as f:
                f.write("TYPE=Ethernet\n")
                f.write("BOOTPROTO=none\n")
                f.write("DEVICE=%s\n" % ethport)
                f.write("ONBOOT=yes\n")
                macaddr = subprocess.getstatusoutput("ifconfig %s | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}'" % ethport)[1]
                f.write("HWADDR=%s\n" % macaddr)
                f.write("MASTER=%s\n" % self.bondnum)
                f.write("SLAVE=yes\n")

    def create_ifcfgbond_file(self):
        '''
        description: this method is create/modify /etc/sysconfig/network-scripts/ifcfg-bondx file      
        '''
        logger.info("create/modify ifcfg-%s" % self.bondnum)
        with open("%s/ifcfg-%s" % (self.netcfgpath,self.bondnum), "w") as f:
            f.write("DEVICE=%s\n" % self.bondnum)
            f.write("TYPE=Bond\n")
            f.write("NAME=%s\n" % self.bondnum)
            f.write("BONDING_MASTER=yes\n")
            f.write("BOOTPROTO=none\n")
            f.write("ONBOOT=yes\n")
            f.write("IPADDR=%s\n" % self.bondip)
            f.write("NETMASK=255.255.255.0\n")
            f.write("GATEWAY=%s.%s.1.1\n" % (self.bondip.split(".")[0],self.bondip.split(".")[1]))
            f.write("STARTMODE=onboot\n")
            f.write('BONDING_OPTS="mode=%s miimon=100 fail_over_mac=1"\n' % int(re.search(r'\d+', self.bondnum, re.I).group(0)))

    def up_port(self):
        '''
        description: this method is up eth port
        params: portstate is {'eth0':netport,'eth1':netport,'bond':bondx}     
        '''
        for k,v in self.portstate.items():
            if v == True:
                os.system("ifconfig %s up >/dev/zero 2>&1" % k)
                os.system("ifup %s >/dev/zero 2>&1" % k)

    def save_eth_file(self):
        '''
        description: this method is save ifcfg-xx file before bond and bond test end can recover net
        '''
        bakflag = True
        for portnm in self.eth:
            foldeth = open("%s/ifcfg-%s" % (self.netcfgpath,portnm))
            oldeth = foldeth.readlines()
            for bondkey in oldeth:
                if re.search(r'MASTER=bond.*', bondkey, re.I):
                    bakflag = False
            if bakflag == True:
                with open("%s/ifcfg-%s-bak" % (self.netcfgpath,portnm), "w") as f:
                    f.writelines(oldeth)       
            foldeth.close()

    def recover_eth_file(self):
        '''
        description: this method is according save_eth_file to recover net
        '''
        recover_flag = True
        for baketh in self.eth:
            if os.path.exists("%s/ifcfg-%s-bak" % (self.netcfgpath,baketh)):
                bondeth_f = open("%s/ifcfg-%s-bak" % (self.netcfgpath,baketh))
                network_f = open("%s/ifcfg-%s" % (self.netcfgpath,baketh), "w")
                network_f.writelines(bondeth_f.readlines())
                bondeth_f.close()
                network_f.close()
                os.system("rm -rf %s/ifcfg-%s-bak" % (self.netcfgpath,baketh))
            else:
                recover_flag = False
                logger.warn("not find ifcfg-%s-bak please manual recover network" % baketh)     
        return recover_flag

    def init(self):
        '''
        description: this method is check env and bonding module
        '''
        logger.info("Try save the old ifcfg file")
        if os.path.exists("%s/ifcfg-%s" % (self.netcfgpath,self.eth0)) and os.path.exists("%s/ifcfg-%s" % (self.netcfgpath,self.eth1)):
            self.save_eth_file()
        else:
            logger.warn("can not find the ifcfg %s" % self.netcfgpath)
        logger.info("check bonding module")
        lsmodstate, lsmodres = subprocess.getstatusoutput("lsmod |grep -i bond")
        if lsmodstate == 0 and lsmodres != "":
            return True
        else:
            probestate, proberes = subprocess.getstatusoutput("modprobe bonding")
            if probestate == 0:
                infostate, infoberes = subprocess.getstatusoutput("modinfo bonding |grep -i description")
                if infostate == 0 and infoberes != "":
                    logger.info(infoberes)
                    return True
                else:
                    logger.error("please check module bonding use modinfo bonding")
                    return False
            else:
                logger.error("modprobe bonding fail")
                return False
    
    def check_bond_state(self):
        checkbond = subprocess.getstatusoutput("cat /proc/net/bonding/%s" % self.bondnum)[1].split("\n")
        checkbondstr = " ".join(checkbond)
        if re.search(r'Slave Interface:\s*%s' % self.eth0, checkbondstr, re.I) and re.search(r'Slave Interface:\s*%s' % self.eth1, checkbondstr, re.I):
            logger.info("%s test over" % self.bondnum)
        else:
            logger.error("%s test fail please check" % self.bondnum)

if __name__ == '__main__':
    bondtest = Bond_net(argspart)
    logpath = baselocallogpath + argspart["bondnum"] 
    logger = Logger(log_file=logpath, stdoutput=False, log_file_timestamp=True)
    if argspart["recover"] == "True":
        bondtest.clear_bond()
        reflag = bondtest.recover_eth_file()
        if reflag == True:
            bondtest.portstate[bondtest.bondnum] = False
            bondtest.up_port()
        exit()
    else:
        bondtest.clear_bond()
        if bondtest.init() == True:
            bondtest.create_ifcfg_file()
            bondtest.create_ifcfgbond_file()
            os.system('echo "alias %s bonding" > /etc/modprobe.d/%s.conf' % (bondtest.bondnum,bondtest.bondnum))
            bondtest.portstate[bondtest.bondnum] = True
            bondtest.up_port()
            bondtest.check_bond_state()
        else:
            exit()
