import sys
import os
import threading
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

import argparse
from common.other.log import Logger
from common.communication.ssh import SSH  
from common.communication.transfer import FileTransfer

pars = argparse.ArgumentParser()
pars.description = "python3 standlone/network/roce_test.py -i '192.168.2.129-192.168.2.242 mlx5_0-mlx5_0' -t 'write read' -s 'user:root password:1' -c 'user:root password:1' -a 'bw lat'"
pars.add_argument("-i", "--serverclientip", required=True, help="input server client ip ex: 'serverip-clientip mlx5_0-mlx5_0:serverip-clientip mlx5_1-mlx5_1'")
pars.add_argument("-t", "--testaction", default='write', help="input test action ex:read,write")
pars.add_argument("-a", "--bwlat", default='bw', help="input test type bw or lat")
pars.add_argument("-s", "--serverinfo", required=True, help="input serverinfo ex: 'user:root password:1' ")
pars.add_argument("-c", "--clientinfo", required=True, help="input clientinfo ex: 'user:root password:1' ")
pars.add_argument("-g", "--gid", required=False,default='0',help="input gid index default 0")
pars.add_argument("-b", "--bidirectional", default="False", help="if need test bidirectional input -b True ")
argspart = vars(pars.parse_args())

if re.search(r'%s' % os.path.abspath('.'), os.path.dirname(__file__), re.I):
    baselocallogpath = os.path.dirname(__file__) + "/result/rocelog/"
else:
    baselocallogpath = os.path.abspath('.') + "/" + os.path.dirname(__file__) + "/result/rocelog/"

class Roce_test():
    '''
    description: this class use to create Roce_test object 
    author: wanglei
    params: server_info,client_info,IP,bwlat,gid,testaction(write or read or send)
    '''
    def __init__(self):
        self.ipkv = argspart['serverclientip'].split(":")
        self.testaction = argspart['testaction'].split(" ")
        self.bwlat = argspart['bwlat'].split(" ")
        self.bi = argspart['bidirectional']
        self.gid = argspart['gid']
        self.server_info = {}
        self.ibvflag = False

        for sertmp in argspart['serverinfo'].split(" "):
            self.server_info[sertmp.split(":")[0]] = sertmp.split(":")[1]
        
        self.client_info = {}
        for clitmp in argspart['clientinfo'].split(" "):
            self.client_info[clitmp.split(":")[0]] = clitmp.split(":")[1]
        

    def ibv_rc_pingpong(self,**kwargs):
        '''
        description: this method is use to test ibv_rc_pingpong
        '''
        if kwargs.get('host') == 'server':
            serverinfotmp = kwargs.get('server')
            ibvserssh = SSH(**serverinfotmp,ip=kwargs.get('serveri'),stdoutput=False,logger=kwargs.get('logger'))
            ibvserssh.cmd("ibv_rc_pingpong -d %s -g %s" % (kwargs.get('serverm'),self.gid))
            #print("ibv_rc_pingpong -d %s -g %s \n" % (kwargs.get('serverm'),self.gid))
        elif kwargs.get('host') == 'client':
            clientinfotmp = kwargs.get('client')
            ibvclissh = SSH(**clientinfotmp,ip=kwargs.get('clienti'),stdoutput=False,logger=kwargs.get('logger'))
            ibv_res = ibvclissh.cmd("ibv_rc_pingpong -d %s %s -g %s" % (kwargs.get('clientm'),kwargs.get('serverip'),self.gid))
            print(ibv_res)
            restmp = " ".join(ibv_res)
            if re.search(r'\d*\sbytes\sin.*seconds\s=\s.*',restmp,re.I) and re.search(r'\d*\siters\sin.*seconds\s=\s.*',restmp,re.I):
                self.ibvflag = True
            #print("ibv_rc_pingpong -d %s %s -g %s \n" % (kwargs.get('clientm'),kwargs.get('serverip'),self.gid))

    def start_ibserver(self,**kwargs):
        '''
        description: this method is use to start ib test server
        '''
        sshserverinfo = kwargs.get("server")
        serverssh = SSH(**sshserverinfo,stdoutput=False,ip=kwargs.get('ip'),logger=kwargs.get('logger'))
        serverssh.cmd("if [[ ! -d /roce_test ]]; then mkdir /roce_test; fi")
        serverssh.cmd("if [[ ! -d /roce_test/%s-server ]]; then mkdir /roce_test/%s-server; fi" % (kwargs.get('ip'),kwargs.get('ip')))
        if self.bi == "True":
            serverssh.cmd("ib_%s_%s -a -b -F -d %s >/roce_test/%s-server/%s-%s-%s-ibserver.log"\
            % (kwargs.get('seract'),kwargs.get('serbl'),kwargs.get('sermlx'),kwargs.get('ip'),kwargs.get('ip'),kwargs.get('seract'),kwargs.get('serbl'))) 
        else:
            #print("ib_%s_%s -a -F -d %s >/roce_test/%s-%s-%s-ibserver.log\n"\
            #% (kwargs.get('seract'),kwargs.get('serbl'),kwargs.get('sermlx'),kwargs.get('ip'),kwargs.get('seract'),kwargs.get('serbl')))

            serverssh.cmd("ib_%s_%s -a -F -d %s >/roce_test/%s-server/%s-%s-%s-ibserver.log"\
            % (kwargs.get('seract'),kwargs.get('serbl'),kwargs.get('sermlx'),kwargs.get('ip'),kwargs.get('ip'),kwargs.get('seract'),kwargs.get('serbl')))
        
    def start_ibclient(self,**kwargs):
        '''
        description: this method is use to start ib test client
        '''
        sshclientinfo = kwargs.get("client")
        clientssh = SSH(**sshclientinfo,stdoutput=False,ip=kwargs.get('ip'),logger=kwargs.get('logger'))
        clientssh.cmd("if [[ ! -d /roce_test ]]; then mkdir /roce_test; fi")
        clientssh.cmd("if [[ ! -d /roce_test/%s-client ]]; then mkdir /roce_test/%s-client; fi" % (kwargs.get('ip'),kwargs.get('ip')))
        if self.bi == "True":
            clientssh.cmd("ib_%s_%s -a -b -F -d %s %s >/roce_test/%s-client/%s-%s-%s-ibclient.log"\
            % (kwargs.get('cliact'),kwargs.get('clibl'),kwargs.get("climlx"),kwargs.get("serverip"),kwargs.get('ip'),kwargs.get('ip'),kwargs.get('cliact'),kwargs.get('clibl')))
        else:
            #print("ib_%s_%s -a -F -d %s %s >/roce_test/%s-client/%s-%s-%s-ibclient.log\n"\
            #% (kwargs.get('cliact'),kwargs.get('clibl'),kwargs.get("climlx"),kwargs.get("serverip"),kwargs.get('ip'),kwargs.get('ip'),kwargs.get('cliact'),kwargs.get('clibl')))
            
            clientssh.cmd("ib_%s_%s -a -F -d %s %s >/roce_test/%s-client/%s-%s-%s-ibclient.log"\
            % (kwargs.get('cliact'),kwargs.get('clibl'),kwargs.get("climlx"),kwargs.get("serverip"),kwargs.get('ip'),kwargs.get('ip'),kwargs.get('cliact'),kwargs.get('clibl')))
        
    def log_save(self,**kwargs):
        '''
        description: this method is use to save ib test log
        '''
        for lip in self.ipkv:
            lipkv,lmlxkv = lip.split(" ")
            serverip,clientip = lipkv.split("-")
            remoteserlogpath = ("/roce_test/%s-server" % serverip)
            remoteclilogpath = ("/roce_test/%s-client" % clientip)
            logdir = baselocallogpath + lipkv
            if not os.path.exists(logdir):
                os.makedirs(logdir)
            else:
                shutil.rmtree(logdir)
                os.makedirs(logdir)
            serscp_obj = FileTransfer(**self.server_info,ip=serverip,logger=kwargs.get('logger'))
            serscp_obj.scp(local=logdir,remote=remoteserlogpath,operation='downloading')
            cliscp_obj = FileTransfer(**self.client_info,ip=clientip,logger=kwargs.get('logger'))
            cliscp_obj.scp(local=logdir,remote=remoteclilogpath,operation='downloading')

            rmserlog = SSH(**self.server_info,ip=serverip,logger=kwargs.get('logger'))
            rmserlog.cmd("rm -rf /roce_test/%s-server" % serverip)
            rmclilog = SSH(**self.client_info,ip=clientip,logger=kwargs.get('logger'))
            rmclilog.cmd("rm -rf /roce_test/%s-client" % clientip)

    def run_test(self):
        logpath = baselocallogpath + "roce"
        testlogger = Logger(log_file=logpath, stdoutput=False, log_file_timestamp=True)
        for ipkvtmp in self.ipkv:
            ipkv,mlxkv = ipkvtmp.split(" ")
            serverip, clientip = ipkv.split("-")
            servermlx,clientmlx = mlxkv.split("-")
            ibst = threading.Thread(target=self.ibv_rc_pingpong,\
            kwargs={'server':self.server_info,'serveri':serverip,'serverm':servermlx,'host':'server','logger':testlogger})
            ibct = threading.Thread(target=self.ibv_rc_pingpong,\
            kwargs={'client':self.client_info,'clienti':clientip,'clientm':clientmlx,'serverip':serverip,'host':'client','logger':testlogger})
            ibst.start()
            time.sleep(2)
            ibct.start()
            ibct.join()
            ibst.join()
            if self.ibvflag:
                for act in self.testaction:
                    for bw_lat in self.bwlat:
                        st = threading.Thread(target=self.start_ibserver,\
                        kwargs={'server':self.server_info,'ip':serverip,'sermlx':servermlx,'seract':act,'serbl':bw_lat,'logger':testlogger})
                    
                        ct = threading.Thread(target=self.start_ibclient,\
                        kwargs={'client':self.client_info,'ip':clientip,'climlx':clientmlx,'serverip':serverip,'sermlx':servermlx,'cliact':act,'clibl':bw_lat,'logger':testlogger})
                        st.start()
                        time.sleep(2)
                        ct.start()
                        ct.join()
                        st.join()
            else:
                print("ibv_rc_pingpong test fail please check")
                testlogger.error("ibv_rc_pingpong test fail please check")
            self.log_save(logger=testlogger)

if __name__ == '__main__':
    roce = Roce_test()
    roce.run_test()
