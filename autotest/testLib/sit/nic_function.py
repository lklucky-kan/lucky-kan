import re
import os
import time
import threading
import subprocess
from autotest.testLib.base import Base
from common.other.log import Logger
from common.communication.ssh import SSH
import pexpect

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

class Nic_function(Base):
    '''
    author: wanglei
    description: this class is create NIC object to test
    params:
    serverinfo :need add -o serverip=0.0.0.0 -o serveruser=xxx -o serverpassword=xxx

    clientinfo :need add -o clientip=0.0.0.0 -o clientuser=xxx -o clientpassword=xxx

    serverport_clientport:this partment for method test_vlan need add -o serverport_clientport='ens17f1:ens17f1' if need test other port 
    -o serverport_clientport='ens17f1:ens17f1 ens17f0:ens17f0'

    clearvlan :this partment for method test_vlan if olny clear port vlan add -o clearvlan='True'

    testcount :input the test cycle counts for test_nic_fwcycle FW update

    fwfile :input the FW file XXXXX.bin

    vfcount :for vf counts test input counts of vf 

    pcie_bus :for fw update cycle -o pcie_bus='/dev/device/mtxxxxx busid-ethport'
    '''    

    def __init__(self, **kwargs):
        '''
        author :wanglei
        description: class init method to init params
        '''

        Base.__init__(self, **kwargs)
        self.result = {}
        self.max_vlan = 0
        self.vlanipkv = {}
        self.mstpcieid = {}
        self.checksession = ''
        self.clear_flag = kwargs.get('clearvlan')
        self.testcount = kwargs.get('testcount')
        self.vfcount = kwargs.get('vfcount')
        self.fwfile = kwargs.get("fwfile")
        mstpcieid = kwargs.get('pcie_bus')
        if mstpcieid:
            mstpcieid = mstpcieid.split(" ")
            for msttmp in mstpcieid:
                self.mstpcieid[msttmp.split('-')[0]] = msttmp.split('-')[1] + "-" + msttmp.split('-')[2]       
        self.serverip = kwargs.get('serverip')
        self.serveruser = kwargs.get('serveruser')
        self.serverpassword = kwargs.get('serverpassword')

        self.clientip = kwargs.get('clientip')
        self.clientuser = kwargs.get('clientuser')
        self.clientpassword = kwargs.get('clientpassword')
        
        self.server_info = self.options.get('server')
        self.server_obj = self.get_obj(self.server_info.get('ip'))

        portnametmp = kwargs.get('serverport_clientport')
        if portnametmp:
            self.portname = portnametmp.split(" ")
        self.nic_log_file = os.path.join(self.log_path, self.testcase + '_other' + '.log')
        self.niclogger = Logger(log_file=self.nic_log_file,log_file_timestamp=False,stdoutput=False)

    def check_host(self):
        '''
        descrption:this method use to check the server if power on,and try 3 times
        return:
        if the host server power on return true else return false
        '''
        key_file = ''
        port = '22'
        prompt=r'\n*\r*[^#]\S+@\S+\s*\S*]#\s*'
        question = '(?i)are you sure you want to continue connecting'
        timeout = 600
        spawn_ssh = "ssh " + key_file + self.serveruser + '@' + self.serverip + " -p " + str(port) 
        self.checksession = pexpect.spawn(spawn_ssh, timeout=timeout)
        retry = 0
        send_passwd_count   = 0
        while True :
            index = self.checksession.expect([pexpect.EOF, pexpect.TIMEOUT, question, 'assword:', r'yes\S+no.*' ,prompt])
            if index == 0:
                retry += 1
                if retry > 3:
                    return False     
                self.checksession = pexpect.spawn(spawn_ssh)
                continue
            if index == 1:
                return False
            if index == 2: 
                self.checksession.sendline ('yes')
                continue
            if index == 3: 
                if send_passwd_count >= 1:
                    return False
                self.checksession.sendline (self.serverpassword)
                send_passwd_count += 1
                continue
            if index == 4:
                self.checksession.sendline ('yes')
            if index == 5:
                self.niclogger.info("session is successfully open")
                return True

    @staticmethod
    def ping_nin(**kwargs):
        '''
        author :wanglei
        description: this method is check server client net status
        params: kwargs is dict
        kwargs = {ip=serverip,user=serveruser,password=serverpassword,clientip=clientip}
        return:
        if net status is ok return True else return False
        '''
        ping_count = 1
        while True:
            if kwargs.get('ip') == 'localhost':
                cmdout = subprocess.getstatusoutput("ping -c 3 %s" % kwargs.get("clientip"))[1]
            else:
                host_seesion = SSH(ip=kwargs.get('ip'),user=kwargs.get('user'),password=kwargs.get('password'),stdoutput=False)
                sshcmdout = host_seesion.cmd("ping -c 3 %s" % kwargs.get("clientip"))
                cmdout = " ".join(sshcmdout) 
                cmdout = str(cmdout)
            if re.search('100% packet loss', cmdout, re.I):
                if kwargs.get('state') == 'onlycheck':
                    kwargs.get("logger").warn("serverip:%s clientip:%s is not available!" % (kwargs.get("ip"),kwargs.get("clientip")))
                else:
                    kwargs.get("logger").error("serverip:%s clientip:%s is not available!" % (kwargs.get("ip"),kwargs.get("clientip")))
                if ping_count > 3:
                    return False
            elif re.search(r'.*\s0% packet loss', cmdout, re.I):
                kwargs.get("logger").info("serverip:%s clientip:%s is OK!" % (kwargs.get("ip"),kwargs.get("clientip")))
                return True
            elif re.search(r'(.*\s[3-6][3-6]% packet loss)', cmdout, re.I):
                if kwargs.get('state') == 'onlycheck':
                    kwargs.get("logger").info(" has networking issue. Please check it!")
                else:
                    kwargs.get("logger").warn(" has networking issue. Please check it!")
                if ping_count > 3:
                    return False
            ping_count += 1

    def check_command(self,checkcmd,seesion):
        '''
        author :wanglei
        description :this method use to check linux command if exist
        params:
        checkcmd :input linux command
        seesion :host SSH class object ex: SSH(ip=serverip,user=serveruser,password=serverpassword,stdoutput=False) 
        return :if command exist return True
        '''
        res = seesion.cmd(checkcmd)
        if re.search(r'command not found',"".join(res),re.I):
            self.niclogger.error("command not found %s" % checkcmd)
            return False
        else:
            return True

    def nic_fw_command_check(self,remote):
        '''
        author :wanglei
        description :this method for test lib test_nic_fwcycle to check mst/ethtool/flint command if exist
        params:
        remote :one SSH object
        return : if need command is exist return True else return False
        '''
        if self.check_command('mst',remote) and self.check_command('ethtool',remote) and self.check_command('flint',remote):
            return True
        else:
            return False
    
    def network_fw_check(self,expectver,seesion,fwcheckport):
        '''
        author :wanglei
        description :this method use to check FW update if sucess
        params:
        expectver :Expected version ex:16_31_1014 you can get from fw file XXXX.bin
        seesion: one SSH object for fw update server
        '''
        getvertmp = "".join(seesion.cmd("ethtool -i %s |grep -i firmware-version" % fwcheckport))
        if re.search(r'\d+.\d+.\d+',getvertmp,re.I):
            getver = re.search(r'\d+.\d+.\d+',getvertmp,re.I).group(0).replace('.','_')
        else:
            self.niclogger.warn("get fw version fail try 3 times")
            return False
        if getver != expectver:
            self.niclogger.warn("network FW check fail expect fw: %s but get fw: %s and try 3 times" % (expectver,getver))
            return False
        else:
            self.niclogger.info("network FW check sucess expect fw: %s but get fw: %s" % (expectver,getver))
            return True

    def vid_sid_get(self,checkport,vsidseesion):
        vid_sid_dict = {}
        for nickey in ['vendor' ,'device', 'subsystem_vendor', 'subsystem_device']:
            vid_sid_dict[nickey] = vsidseesion.cmd('cat /sys/class/net/%s/device/%s' % (checkport,nickey))
        return vid_sid_dict

    def ping_stress(self):
        self.niclogger.info("ping %s" % self.clientip)
        self.checksession.sendline("ping %s" % self.clientip)

    def fw_flush_function(self,netfwfile,oldpcienum):
        '''
        author :wanglei
        description :this method use to update network FW
        params:
        netfwfile :input a network FW file to update XXXX.bin
        '''
        self.niclogger.info("mst start")
        seesion = SSH(ip=self.serverip,user=self.serveruser,password=self.serverpassword,stdoutput=False)
        seesion.cmd('mst start')
        for pcieidtmp,busid in self.mstpcieid.items():
            expectver = re.search(r'\d+_\d+_\d+',netfwfile,re.I).group(0)
            oldvid_sid = self.vid_sid_get(busid.split('-')[1],vsidseesion=seesion)
            self.check_host()
            pingstress = threading.Thread(target=self.ping_stress)
            pingstress.start()
            time.sleep(5)
            self.niclogger.info("flint --yes -d %s -i %s b" % (pcieidtmp,netfwfile))
            seesion.cmd("flint --yes -d %s -i %s b" % (pcieidtmp,netfwfile))
            time.sleep(5)
            self.check_host()
            self.niclogger.info("ipmitool power cycle")
            self.checksession.sendline("ipmitool power cycle")
            time.sleep(200)
            while not self.check_host():
                self.niclogger.info("waiting......")
                time.sleep(50)
            time.sleep(10)
            self.check_nic_state(oldportnum=oldpcienum,seesion=seesion)
            newvid_sid = self.vid_sid_get(busid.split('-')[1],vsidseesion=seesion)
            for idk,idv in oldvid_sid.items():
                if newvid_sid[idk] != idv:
                    self.niclogger.error("check vid sid fail %s" % busid.split('-')[1])
                    self.niclogger.error("before test: %s after test %s" % (oldvid_sid,newvid_sid))
            if not self.network_fw_check(expectver=expectver,seesion=seesion,fwcheckport=busid.split('-')[1]):
                return False
            self.niclogger.info("lspci -s %s -vvv" % busid.split("-")[0])
            self.niclogger.info("\n".join(seesion.cmd("lspci -s %s -vvv" % busid.split("-")[0])))
            return True
            
    def check_nic_state(self,oldportnum,seesion):
        '''
        author :wanglei
        description :check network DUT HW net prot counts and check if can ping 
        params:
        oldportnum :before update FW file the old DUT HW net port counts
        seesion :one SSH object for fw update server
        '''
        newportnum = seesion.cmd("lspci | grep -i eth | wc -l")
        if oldportnum != newportnum:
            self.niclogger.error("check dut HW port num fail before test count %s after test count %s" % (oldportnum,newportnum))
            self.niclogger.error("\n".join(seesion.cmd("lspci | grep -i eth")))
        else:
            self.niclogger.info("check dut HW port num success")
        Nic_function.ping_nin(ip=self.serverip,user=self.serveruser,password=self.serverpassword,clientip=self.clientip,logger=self.niclogger,state='onlycheck')
      
    def test_nic_fwcycle(self):
        '''
        author :wanglei
        description :this method is for test case :network fw update cycle
        use:
        python3 standalone/local_case_runner.py -i name=test_nic_fwcycle -o serverip=192.168.32.129 -o serverpassword=123456 -o serveruser=root 
        -o clientip=192.168.32.129 -o testcount=123456 -o fwfile='/home/fw-ConnectX5-rel-16_30_1004-MCX512A-ACA_Ax_Bx-UEFI-14.23.17-FlexBoot-3.6.301.bin 
        /home/fw-ConnectX5-rel-16_31_1014-MCX512A-ACA_Ax_Bx-UEFI-14.24.13-FlexBoot-3.6.403.bin' -o pcie_bus='/dev/mst/mt4119_pciconf0-0000:01:00.0-enp1s0f0'
        params :none
        return :if fw update cycle test pass return dict self.result pass else return self.result fail and add fail reason 
        '''
        self.result['result'] = "pass"
        self.result['reason'] = ""
        trytimes = 1
        fwseesion = SSH(ip=self.serverip,user=self.serveruser,password=self.serverpassword,stdoutput=False)
        if self.nic_fw_command_check(fwseesion):
            oldportnum = fwseesion.cmd("lspci | grep -i eth | wc -l")
            for num in range(1,int(self.testcount) + 1):
                self.niclogger.info("nic fw testcycle: %s" % num)
                while not self.fw_flush_function(netfwfile=self.fwfile.split(" ")[0],oldpcienum=oldportnum) and trytimes < 4:  
                    trytimes = trytimes + 1
                if trytimes > 3:
                    self.niclogger.error("try times more then 3 fw update fail..........")
                trytimes = 1
                while not self.fw_flush_function(netfwfile=self.fwfile.split(" ")[1],oldpcienum=oldportnum) and trytimes < 4:  
                    trytimes = trytimes + 1
                if trytimes > 3:
                    self.niclogger.error("try times more then 3 fw update fail..........")                
                trytimes = 1
                if self.log_check():
                    pass
                else:
                    self.result['result'] = "fail"
                    self.result['reason'] = "find error in %s please check" % self.nic_log_file
                    return self.result  
        else:
            self.result['result'] = "fail"
            self.result['reason'] = "command not find check log %s" % self.nic_log_file
        return self.result

    def compare_vfcount(self,getvfc):
        """
        author :wanglei
        description :this method compare input vf counts create vf counts equal
        params:
        getvfc :after run create vf counts command ,get vf counts
        """
        if self.vfcount != getvfc:
            self.niclogger.error("check vf count fail input vfcounts %s but get vfcounts %s" % (self.vfcount,getvfc))
        else:
            self.niclogger.info("check vf count sucess input vfcounts %s get vfcounts %s" % (self.vfcount,getvfc))

    
    def test_create_VF(self):
        """
        author :wanglei
        description :test method for SR-IOV
        return :if create vf counts equal input vf counts and dmesg not find key words the result return pass
        """
        vfseesion = SSH(ip=self.serverip,user=self.serveruser,password=self.serverpassword,stdoutput=False)
        self.niclogger.info("dmesg -c")
        vfseesion.cmd('dmesg -c')
        self.niclogger.info("lspci|grep -i eth |wc -l")
        self.niclogger.info("".join(vfseesion.cmd("lspci|grep -i eth |wc -l")))
        self.niclogger.info("\n".join(vfseesion.cmd('lspci|grep -i eth')))
        
        self.niclogger.info('echo %s > /sys/class/net/eth0/device/sriov_numvfs' % self.vfcount)
        vfseesion.cmd('echo %s > /sys/class/net/eth0/device/sriov_numvfs' % self.vfcount)
        
        self.niclogger.info('lspci |grep -i "virtual function" |wc -l')
        vfres = "".join(vfseesion.cmd('lspci |grep -i "virtual function" |wc -l'))
        self.compare_vfcount(vfres)

        self.niclogger.info('dmesg|egrep -i "error|fail|warn|wrong|bug|respond|pending"')
        dmesginfo = vfseesion.cmd('dmesg|egrep -i "error|fail|warn|wrong|bug|respond|pending"')
        if dmesginfo:
            self.niclogger.error("find key words in dmesg log please check %s" % self.nic_log_file)
            self.niclogger.error("\n".join(dmesginfo))
        else:
            self.niclogger.info("check dmesg log sucess")

        if self.log_check():
            self.result['result'] = 'pass'
            self.result['reason'] = ''
        else:
            self.result['result'] = 'fail'
            self.result['reason'] = 'find error in %s' % self.nic_log_file
        
        return self.result

    def check_vlan(self,cssh):
        '''
        author :wanglei
        description :this method use to check eth vlan and clear
        params:
        cssh :one SSH object for need check and clear server
        cnetname :need check and clear port ex:ens33 or ens17f0
        '''
        oldvlanlist = []
        nettmp = cssh.cmd("ls /sys/class/net |tr '\n' ' '")
        if nettmp[-1] == "":
            nettmp.pop[-1]
        for vlantmp in nettmp:
            oldvlan = vlantmp.split(" ")
        for vlan in oldvlan:
            if re.search(r'\S+\.\d+',vlan,re.I):
                oldvlanlist.append(vlan)
        if oldvlanlist:
            for delvlan in oldvlanlist:
                cssh.cmd("ip link delete %s type vlan" % delvlan) 
    
    def get_maxvlan(self,ssh,netname):
        '''
        author :wanglei
        description :this method use to add vlan and get the max vlan counts
        params:
        ssh :one SSH object for need add vlan and get max vlan counts server
        return :return netport max vlan counts
        '''
        num = 1
        while True:
            res_setvlan = ssh.cmd('ip link add link %s name %s.%s type vlan id %s'\
            % (netname,netname,num,num))
            if re.search(r'.*Invalid VLAN id.*'," ".join(res_setvlan),re.I):
                break
            else:
                num = num + 1
        num = num - 1
        return num

    def set_ip(self,**kwargs):
        '''
        author :wanglei
        description :this method use to set vlan port ip
        params:
        kwargs is a dict include network number :xx hostnum :host number vlanid :xx
        '''
        kwargs.get('ssh').cmd("ip addr add 192.168.%s.%s/24 dev %s.%s"\
        % (kwargs.get('network'),kwargs.get('hostnum'),kwargs.get('netname'),kwargs.get('vlanid')))

        self.niclogger.info("ip addr add 192.168.%s.%s/24 dev %s.%s %s"\
        % (kwargs.get('network'),kwargs.get('hostnum'),kwargs.get('netname'),kwargs.get('vlanid'),kwargs.get('host')))

        #kwargs.get('ssh').cmd("ip link set %s.%s up" % (kwargs.get('netname'),kwargs.get('vlanid')))
    
    def get_ethname(self,**kwargs):
        '''
        author :wanglei
        description :this method use to according ip to get eth name and ethinfo
        params :
        kwargs is a dict include one SSH object for get info server and server ip
        return : return eth name and netport info
        '''
        ethinfo = " ".join(kwargs.get('getssh').cmd("ip a |grep -i %s/" % kwargs.get("ip")))
        eth = ethinfo.split(" ")[-1]       
        return eth,ethinfo

    def check_ping(self,**kwargs):
        '''
        author :wanglei
        description :this method use to up server/client vlan port check vlan ping and down vlan port 
        params:
        kwargs is a dict include two SSH object one is server and another is client , server vlan ip and client vlan ip    
        '''
        servername,sernameinfo = self.get_ethname(ip=kwargs.get("serverip"),getssh=kwargs.get('serssh'))
        self.niclogger.info(sernameinfo)
        clientname,clinameinfo = self.get_ethname(ip=kwargs.get("clientip"),getssh=kwargs.get('clissh'))
        self.niclogger.info(clinameinfo)
        self.niclogger.info("ip link set %s up" % servername)
        self.niclogger.info("ip link set %s up" % clientname)
        kwargs.get('serssh').cmd("ip link set %s up" % servername)
        kwargs.get('clissh').cmd("ip link set %s up" % clientname)
        ping_count = 1
        while True:
            ip_seesion = kwargs.get('serssh')
            sshcmdout = ip_seesion.cmd("ping -c 3 %s" % kwargs.get("clientip"))
            cmdout = " ".join(sshcmdout) 
            cmdout = str(cmdout)
            if re.search('100% packet loss', cmdout, re.I):
                if ping_count > 3: 
                    self.niclogger.error("serverip:%s clientip:%s is not available!" % (kwargs.get("serverip"),kwargs.get("clientip")))
                    break
                else:
                    self.niclogger.info("serverip:%s clientip:%s is not available! and try" % (kwargs.get("serverip"),kwargs.get("clientip")))
            elif re.search(r'.*\s0% packet loss', cmdout, re.I):
                self.niclogger.info("serverip:%s clientip:%s is OK!" % (kwargs.get("serverip"),kwargs.get("clientip")))
                self.niclogger.info("\n".join(sshcmdout))
                break
            elif re.search(r'(.*\s[3-6][3-6]% packet loss)', cmdout, re.I):
                if ping_count > 3:
                    self.niclogger.warn(" has networking issue. Please check it!")
                    break
                else:
                    self.niclogger.info("packet loss and try")
            ping_count += 1

        self.niclogger.info("ip link set %s down" % servername)
        self.niclogger.info("ip link set %s down" % clientname)
        self.niclogger.info("\n")
        kwargs.get('serssh').cmd("ip link set %s down" % servername)
        kwargs.get('clissh').cmd("ip link set %s down" % clientname)
    
    def log_check(self,onlyerror=True):
        '''
        author :wanglei
        description :this method is check test log if find error
        return : if log not find error or warning return True   
        '''
        f = open(self.nic_log_file)
        for loginfo in f.readlines():
            if onlyerror:
                if re.search(r'.*ERROR:.*', loginfo, re.I):
                    return False
            else:
                if re.search(r'.*ERROR:.*', loginfo, re.I) or re.search(r'.*WARNING:.*', loginfo, re.I):
                    return False
        return True

    def test_vlan(self):
        '''
        author :wanglei
        description: this method is create vlan and check ping
        use :
        python3 standalone/local_case_runner.py -i name=test_vlan -o serverip=192.168.2.242 -o serverpassword=1 
        -o serveruser=root -o serverport_clientport='ens17f1:enp1s0f1' -o clientip=192.168.2.129 -o clientpassword=1 
        -o clientuser=root (-o clearvlan='True')optional only need clear vlan 
        '''        
        self.result['result'] = "pass"
        self.result['reason'] = ""
        netnum = 1
        hostnumtmp = 1
        threadlist = []
        serverssh = SSH(password=self.serverpassword,user=self.serveruser,ip=self.serverip,stdoutput=False)
        clientssh = SSH(password=self.clientpassword,user=self.clientuser,ip=self.clientip,stdoutput=False)
        sercheck_vlant = MyThread(self.check_vlan,args=(serverssh,))
        clicheck_vlant = MyThread(self.check_vlan,args=(clientssh,))
        if self.clear_flag == "True":
            sercheck_vlant.start()
            clicheck_vlant.start()
            sercheck_vlant.join()
            clicheck_vlant.join()
        else:
            sercheck_vlant.start()
            clicheck_vlant.start()
            sercheck_vlant.join()
            clicheck_vlant.join()
            for port_name in self.portname:
                vlan_ip = []
                serport,cliport = port_name.split(":")
                sermaxthread = MyThread(self.get_maxvlan, args=(serverssh,serport))
                climaxthread = MyThread(self.get_maxvlan, args=(clientssh,cliport))
                sermaxthread.start()
                climaxthread.start()
                sermaxthread.join()
                climaxthread.join()
                sermaxvlan = sermaxthread.get_result()
                climaxvlan = climaxthread.get_result()
                if sermaxvlan != climaxvlan:
                    self.result['result'] = "fail"
                    self.result['reason'] = "find server maxvlan %s %s != client maxvlan %s %s" % (serport,sermaxvlan,cliport,climaxvlan)
                    return self.result
                else:
                    self.max_vlan = sermaxvlan
                    self.niclogger.info("the max vlan counts is %s" % self.max_vlan)
                for vlan_num in range(1,self.max_vlan+1):
                    hostnumtmp = hostnumtmp + 1
                    self.set_ip(ssh=serverssh,netname=serport,vlanid=vlan_num,hostnum=hostnumtmp,network=netnum,host='server')
                    servervlanip = '192.168.' + str(netnum) + '.' + str(hostnumtmp)
                    hostnumtmp = hostnumtmp + 1
                    self.set_ip(ssh=clientssh,netname=cliport,vlanid=vlan_num,hostnum=hostnumtmp,network=netnum,host='client')
                    clientvlanip = '192.168.' + str(netnum) + '.' + str(hostnumtmp)
                    vlan_ip.append(servervlanip + ':' + clientvlanip)
                    if hostnumtmp > 250:
                        netnum = netnum + 1
                        if netnum == int(self.serverip.split('.')[2]) or netnum == int(self.clientip.split('.')[2]):
                            netnum = netnum + 1
                        hostnumtmp = 1 
                self.vlanipkv[port_name] = vlan_ip   
        if self.clear_flag == "True":
            self.result['result'] = "pass"
            self.result['reason'] = "only clean vlan"
        else:
            for ipk,ipv in self.vlanipkv.items():
                for i in ipv:
                    self.check_ping(serverip=i.split(':')[0],clientip=i.split(':')[1],serssh=serverssh,clissh=clientssh)
            if self.log_check():
                pass
            else:
                self.result['result'] = "fali"
                self.result['reason'] = "find error in %s please check" % self.nic_log_file
        return self.result

    def test_ethbond(self):
        '''
        author :wanglei
        description: this method is for local_case_runner to bond test
        use :
        python3 standalone/local_case_runner.py -i name=test_udp_netperf,script_opt="-n 'ens33 ens37' -b bond1 -i 192.168.2.10"
        -n which port to bond 
        -b bondtype ex:bond0 bond1 bond2
        -i bondip ex:192.168.xxx.xxx
        '''
        bondnum = ""
        self.result['result'] = "fail"
        self.result['reason'] = ""        
        script_opt = self.options.get('testcase', {}).get('script_opt', '')
        self.server_obj.run_script('standalone/network/nic_bond_function.py', opts=script_opt, program='python3')
        for part in script_opt.split(" "):
            if re.search(r'bond\d+', part, re.I):
                bondnum = part
                break
        if bondnum == "":
            bondnum = "bond0"
        if "True" in script_opt:
            self.result['result'] = "pass"
        else:
            checkbond = self.server_obj.cmd("cat /proc/net/bonding/%s" % bondnum)
            checkbondstr = " ".join(checkbond)
            eth0,eth1 = str(script_opt).split("'")[1].split(" ")
            if re.search(r'Slave Interface:\s*%s' % eth0, checkbondstr, re.I) and re.search(r'Slave Interface:\s*%s' % eth1, checkbondstr, re.I):
                self.result['result'] = "pass"
            else:
                self.result['reason'] = "check /proc/net/bonding/%s fail" % bondnum
        return self.result

    def test_udp_netperf(self):
        '''
        author :wanglei
        description: this method is for local_case_runner to netperf udp test
        use:
        python3 standalone/local_case_runner.py -i name=test_udp_netperf,script_opt="-i '192.168.32.128-192.168.32.129' 
        -s 'user:root password:123456' -c 'user:root password:123456' -d '60' -t 2 -l '64'"

        -i serverip_clientip ex:192.168.32.128 is serverip 192.168.32.129 is clientip, if need other netserver netperf -i
        '192.168.32.128-192.168.32.129 192.168.32.131-192.168.32.132'
        -s serverinfo 
        -c clientinfo
        -d test time 
        -t test threads 
        -l netperf pkg length 
        '''
        self.result['result'] = "pass"
        self.result['reason'] = "" 
        script_opt = self.options.get('testcase', {}).get('script_opt', '')
        scriptlist = script_opt.split("'")
        for part in scriptlist:
            if re.search(r'-i',part,re.I):
               ipkvindex = scriptlist.index(part) + 1 
        self.server_obj.run_script('standalone/network/netperf_udp_test.py', opts=script_opt, program='python3')
        ipkv = scriptlist[ipkvindex].split(" ")
        for ipkvtmp in ipkv:
            netperflogdir = self.server_obj.cmd("ls standalone/network/result/netperf/%s |grep -i netperf" % ipkvtmp)
            for perflog in netperflogdir:
                f = open("standalone/network/result/netperf/%s/%s" % (ipkvtmp,perflog))
                for loginfo in f.readlines():
                    if re.search(r'.*ERROR:.*', loginfo, re.I) or re.search(r'.*WARNING:.*', loginfo, re.I):
                         self.result['result'] = "fail"
                         self.result['reason'] = "find log standalone/network/result/netperf/%s/%s error/warning please check"\
                         % (ipkvtmp,perflog)
                f.close()
        return self.result 
