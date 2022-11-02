import argparse
import os
import subprocess
import re
import sys
import pprint
tea_path = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.pardir,
        os.pardir
        )
)
sys.path.append(tea_path)
from common.other.log import Logger
from common.communication.ssh import SSH  
from common.communication.transfer import FileTransfer
import threading
import random
from datetime import datetime
import shutil

pars = argparse.ArgumentParser()
pars.description="python3 standalone/network/netperf_udp_test.py -i '192.168.2.129-192.168.2.242' -s 'user:root password:1' -c 'user:root password:1' -d 30 -t 3 -l '64 512'"
pars.add_argument("-i", "--serverip_clientip", required=True, help="please input serverip clientip ex: -i 'serverip-clientip serverip-clientip'")
pars.add_argument("-s", "--serverinfo", required=True, help="input the serverinfo ex: -s 'user:root password:123'")
pars.add_argument("-c", "--clientinfo", required=True, help="input the clientinfo ex: -s 'user:root password:123'")
pars.add_argument("-d", "--testtime", required=True,help="please input netperf test time")
pars.add_argument("-t", "--threads",required=False,default='2',help="please input netperf threads")
pars.add_argument("-l", "--length", required=False,help="input the package length")
pars.add_argument("-n", "--cyclenumber", required=False,default='1',help="input netperf test cycle test")
pars.add_argument("-m", "--mtu",required=False,default="9000 1500",help='input mtu value default "1500 9000"')

argspart = vars(pars.parse_args())
partkwargs = {}
partkwargs.update(server_clientip=argspart["serverip_clientip"])
partkwargs.update(server_info=argspart["serverinfo"])
partkwargs.update(client_info=argspart["clientinfo"])
partkwargs.update(length=argspart["length"])
partkwargs.update(mtu=argspart["mtu"])
partkwargs.update(testtime=argspart["testtime"])
partkwargs.update(thread=argspart["threads"])
partkwargs.update(cyclenumber=argspart["cyclenumber"])

if re.search(r'%s' % os.path.abspath('.'), os.path.dirname(__file__), re.I):
    baselocallogpath = os.path.dirname(__file__) + "/result/netperf/"
else:
    baselocallogpath = os.path.abspath('.') + "/" + os.path.dirname(__file__) + "/result/netperf/"

class UDP_test():
    '''
    description: this class use to create UDP_test object 
    author: wanglei
    params: server_info,client_info,IP,mtu,package len,test time 
    '''
    def __init__(self,**kwargs):
        self.perfport = []
        self.threadlist = []
        self.sshserobj = []
        self.log = {}
        self.thread = int(kwargs.get("thread")) - 1
        length = kwargs.get("length")
        self.cyclenumber = kwargs.get("cyclenumber")
        if length:
            self.length = kwargs.get("length").split(" ")
        else:
            self.length = []
        self.mtu = kwargs.get('mtu').split(" ")
        self.time = kwargs.get('testtime')
        self.ipkey_value = kwargs.get('server_clientip').split(" ")
        for index in range(len(self.ipkey_value)):
            while True:
                randPortNum = random.randint(12865,49999)
                if os.popen("netstat -anp | grep %d" % randPortNum).read() == "":
                    self.perfport.append(str(randPortNum))
                    break    

        self.server_info = {}
        self.server_info['name'] = "server"
        for serverinfo in kwargs.get('server_info').split(" "):
            serverkey,serverval = serverinfo.split(":")
            self.server_info[serverkey] = serverval

        self.client_info = {}
        self.client_info['name'] = "client"
        for clientinfo in kwargs.get('client_info').split(" "):
            clinetkey,clinetval = clientinfo.split(":")
            self.client_info[clinetkey] = clinetval

    @staticmethod
    def ping_nin(**kwargs):
        '''
        description: this method is check server client net status
        '''
        ping_count = 1
        while True:
            ip_seesion = SSH(**kwargs,ip=kwargs.get("serverip"),stdoutput=False)
            sshcmdout = ip_seesion.cmd("ping -c 3 %s" % kwargs.get("clientip"))
            cmdout = " ".join(sshcmdout) 
            cmdout = str(cmdout)
            if re.search('100% packet loss', cmdout, re.I):
                if ping_count > 3:
                    kwargs.get("logger").error("serverip:%s clientip:%s is not available!" % (kwargs.get("serverip"),kwargs.get("clientip")))
                    return False       
            elif re.search(r'.*\s0% packet loss', cmdout, re.I):
                kwargs.get("logger").info("serverip:%s clientip:%s is OK!" % (kwargs.get("serverip"),kwargs.get("clientip")))
                return True
            elif re.search(r'(.*\s[3-6][3-6]% packet loss)', cmdout, re.I):
                if ping_count > 3:
                    kwargs.get("logger").warn(" has networking issue. Please check it!")
                    return False
            ping_count += 1

    def set_mtu(self,clientobj,clientip,serverobj,serverip,mtu):
        '''
        description: this method is set mtu value
        '''
        serverethinfo = " ".join(serverobj.cmd("ip a |grep -i %s" % serverip))
        servereth = serverethinfo.split(" ")[-1]
        serverobj.cmd("ifconfig %s mtu %s" % (servereth,mtu))
        
        clientethinfo = " ".join(clientobj.cmd("ip a |grep -i %s" % clientip))
        clienteth = clientethinfo.split(" ")[-1]
        clientobj.cmd("ifconfig %s mtu %s" % (clienteth,mtu))


    def clean_server_sar(self):        
        '''
        description: this method is clean all netserver and sar process after netperf test
        '''
        for sshobjtmp in self.sshserobj:
            sshobjtmp.cmd("rm -rf /netperf_result/*")
            sshobjtmp.cmd("killall netserver")
            sshobjtmp.cmd("killall sar")


    def start_end_sar(self,lens,sshobject,seflag,ip,count,mtu):
        '''
        description: this method is start and end sar 
        '''
        if seflag == "True":
            sarpid = sshobject.cmd("sar -n DEV 2 1000 >>/netperf_result/%s/%s-%s-count%s-mtu%sserver.log &" % (ip,ip,lens,count,mtu))
        elif seflag == "False":
            sshobject.cmd("killall sar")

    def start_server(self,**kwargs):
        '''
        description: this method is start netserver process 
        '''
        port = self.perfport.pop(0)
        serverseesion = SSH(**kwargs,stdoutput=False)
        serverseesion.cmd("if [[ ! -d /netperf_result ]]; then mkdir /netperf_result; fi")
        serverseesion.cmd("if [[ ! -d /netperf_result/%s ]]; then mkdir /netperf_result/%s; fi" % (kwargs.get('ip'),kwargs.get('ip')))
        out = serverseesion.cmd("netstat -lntp |grep -i %s" % port)
        if not out:
            print("start netserver on the %s-%s" % (kwargs.get('ip'),port))
            serverseesion.cmd("netserver -p %s" % port)
        return port,serverseesion
    
    
    def save_log(self,**kwargs):
        '''
        description: this method is save sar log after netperf test  
        '''
        for ipkv in self.ipkey_value:
            logserverip = ipkv.split("-")[0]
            remotelogpath = "/netperf_result/%s" % (logserverip)
            locallogpath = baselocallogpath + ipkv
            scp_obj = FileTransfer(**kwargs,ip=logserverip,logger=self.log.get(logserverip))
            scp_obj.scp(local=locallogpath,remote=remotelogpath,operation='downloading')
            """
            conn = fabric.Connection(logserverip , user = self.server_info.get('user'), connect_kwargs={"password": self.server_info.get('password')})
            print("log saveing")
            res = conn.run('ls %s' % remotelogpath)
            logfile = res.stdout.split("\n")
            for logtmp in logfile:
                if logtmp != "":
                    remote = remotelogpath + "/" + logtmp
                    local = locallogpath + ipkv + "/" + logtmp
                    conn.get(remote,local)
            conn.close()
            """

    def start_client(self,**kwargs):
        '''
        description: this method is start netperf process
        '''
        cmd1 = ""
        cmd2 = ""
        t = 0
        clientsshinfo = kwargs.get('cilentin')
        serverssh = kwargs.get("sshobj")
        clientseesion = SSH(**clientsshinfo,stdoutput=True,ip=kwargs.get("ip"),logger=kwargs.get("logger"))
        #ethinfo = " ".join(clientseesion.cmd("ip a |grep -i %s" % kwargs.get("ip")))
        #eth = ethinfo.split(" ")[-1]
        #speedtmp = " ".join(clientseesion.cmd("ethtool %s |grep -i speed" % eth)).strip().split(":")[-1].strip()
        #speed = re.search(r'\d+',speedtmp,re.I).group(0)
        for mtu in self.mtu:
            i = 0
            self.set_mtu(clientseesion,kwargs.get('ip'),serverssh,kwargs.get('serverip'),mtu)
            while i < int(self.cyclenumber):
                for let in self.length:
                    if int(let) != 0 and int(let) != 1460 and int(let) != 8960:
                        self.start_end_sar(let,serverssh,seflag="True",ip=kwargs.get("serverip"),count=i,mtu=mtu)
                        while t < int(self.thread):
                            cmdtmp = "netperf -H %s -p %s -t UDP_STREAM -l %s -- -m %s -M %s & " % (kwargs.get("serverip"),kwargs.get("serverport"),self.time,let,let)
                            cmd1 = cmd1 + cmdtmp
                            t = t + 1
                        cmd2 = "netperf -H %s -p %s -t UDP_STREAM -l %s -- -m %s -M %s " \
                        % (kwargs.get("serverip"),kwargs.get("serverport"),self.time,let,let)

                    elif int(let) == 0:
                        self.start_end_sar(let,serverssh,seflag="True",ip=kwargs.get("serverip"),count=i,mtu=mtu)
                        while t < int(self.thread):
                            cmdtmp = "netperf -H %s -p %s -t UDP_STREAM -l %s & " % (kwargs.get("serverip"),kwargs.get("serverport"),self.time)
                            cmd1 = cmd1 + cmdtmp
                            t = t + 1
                        cmd2 = "netperf -H %s -p %s -t UDP_STREAM -l %s" % (kwargs.get("serverip"),kwargs.get("serverport"),self.time)

                    elif int(let) == 1460 and int(mtu) == 1500:
                        self.start_end_sar(let,serverssh,seflag="True",ip=kwargs.get("serverip"),count=i,mtu=mtu)
                        while t < int(self.thread):
                            cmdtmp = "netperf -H %s -p %s -t UDP_STREAM -l %s -- -m 1460 -M 1460 & " % (kwargs.get("serverip"),kwargs.get("serverport"),self.time)
                            cmd1 = cmd1 + cmdtmp
                            t = t + 1
                        cmd2 = "netperf -H %s -p %s -t UDP_STREAM -l %s -- -m 1460 -M 1460 " \
                        % (kwargs.get("serverip"),kwargs.get("serverport"),self.time)

                    elif int(let) == 8960 and int(mtu) == 9000:
                        self.start_end_sar(let,serverssh,seflag="True",ip=kwargs.get("serverip"),count=i,mtu=mtu)
                        while t < int(self.thread):
                            cmdtmp = "netperf -H %s -p %s -t UDP_STREAM -l %s -- -m 9000 -M 9000 & " % (kwargs.get("serverip"),kwargs.get("serverport"),self.time)
                            cmd1 = cmd1 + cmdtmp
                            t = t + 1
                        cmd2 = "netperf -H %s -p %s -t UDP_STREAM -l %s -- -m 9000 -M 9000 " \
                        % (kwargs.get("serverip"),kwargs.get("serverport"),self.time)                               

                    cmdl = (cmd1) + (cmd2)
                    clientseesion.cmd(cmdl)
                    self.start_end_sar(let,serverssh,seflag="False",ip=kwargs.get("serverip"),count=i,mtu=mtu)
                    t = 0
                    cmd1 = ""
                i = i + 1
      
    def run_test(self):
        for iptmp in self.ipkey_value:
            logdir = baselocallogpath + iptmp
            if not os.path.exists(logdir):
                os.makedirs(logdir)
            else:
                shutil.rmtree(logdir)
                os.makedirs(logdir)
            logpath = logdir + "/" + "netperf"
            testlogger = Logger(log_file=logpath, stdoutput=False, log_file_timestamp=True)
            serverip,clientip = iptmp.split("-")
            self.log[serverip] = testlogger
            if self.ping_nin(**self.server_info,serverip=serverip,clientip=clientip,logger=testlogger):
                serport,sshobj = self.start_server(**self.server_info,ip=serverip,logger=testlogger)
                self.sshserobj.append(sshobj)
                t = threading.Thread(target=self.start_client, kwargs={'cilentin':self.client_info, 'ip':clientip,'serverport':serport, 'logger':testlogger, 'sshobj':sshobj,'serverip':serverip})
                self.threadlist.append(t)
        while self.threadlist:
            clienthread = self.threadlist.pop(0)
            clienthread.start()
            clienthread.join()
        self.save_log(**self.server_info)
        self.clean_server_sar()
        
if __name__ == '__main__':
    objudp = UDP_test(**partkwargs)
    objudp.run_test()
