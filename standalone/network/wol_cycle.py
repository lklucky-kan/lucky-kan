import os 
import subprocess
import argparse
import os
import signal
import time
import re
import threading
from common.other.log import Logger

pars = argparse.ArgumentParser()
pars.description="please input the parameter"
pars.add_argument("-c", "--count", required=False, help="You must enter this parameter to determine")
pars.add_argument("-n", "--osip", required=False, help="network IP addr")
pars.add_argument("-u", "--osuser", default="root", help="os username default:root")
pars.add_argument("-p", "--password", help="os password")
pars.add_argument("-N", "--BMCIP", help="bmc ip")
pars.add_argument("-U", "--bmcusername",default="admin", help="bmc username default:admin")
pars.add_argument("-P", "--bmcpassword",default="admin", help="bmc password default:admin")
pars.add_argument("-W", "--wolcmdaddr", default="10.49.29.255 b0:7b:25:af:1d:a0", help="input wol addr like 10.49.29.255 b0:7b:25:af:1d:a0")
pars.add_argument("-l", "--logpath", help="please input the log path", default="./wol_on_log")
args = vars(pars.parse_args())

NICIP = args["osip"]
osuser = args["osuser"]
ospassword = args["password"]
BMCIP = args["BMCIP"]
bmcuser = args["bmcusername"]
bmcpassword = args["bmcpassword"]
xconunts = int(args["count"])
host = args["wolcmdaddr"].split(' ')[0]
mac = args["wolcmdaddr"].split(' ')[1]
powercount = 0
serverstate = ''
logpath = args["logpath"]
logger = Logger(log_file=logpath, stdoutput=True, log_file_timestamp=True)

class MyThread(threading.Thread):
    '''
    description: this class use to create logchck thread
    '''
    def __init__(self, func):
        super(MyThread, self).__init__()
        self.func = func

    def run(self):
        self.result = self.func()

    def get_result(self):
        try:
            return (self.result[0], self.result[1])
        except Exception:
            return None

        return None

class Test_wol_check():

    '''
    description: this class use to check runing log during testing
    '''
    def __init__(self, **kwargs):
        self.logpath = kwargs.get("logfile")
        self.pid = kwargs.get("script_pid",None)
        self.result = 'pass'
        self.reason = ''

    def pid_check(self):
        pid_state, pid_result = subprocess.getstatusoutput("ps -e |grep -i %s" % str(self.pid))
        if pid_state == 0 and pid_result != '':
            return True
        else:
            return False

    def wol_runstate(self):
        runstate, runlog = subprocess.getstatusoutput("tail -n1 %s" % self.logpath)
        if runstate == 0 and runlog != '':
            if re.search(r'.+\swol cycle test done', runlog, re.I):
                return False
            else:
                return True
        else:
            self.result = 'fail'
            self.reason = ('No wol log please check %s' % self.logpath)
            return False
        
    def log_check(self):
        time.sleep(350)
        while self.wol_runstate():
            logstate, logout = subprocess.getstatusoutput("cat %s" % self.logpath)
            if logstate == 0 and logout != '':
                for logline in logout.split('\n'):
                    if re.search(r'ERROR', logline, re.I) or re.search(r'WARNING', logline, re.I):
                        self.result = 'fail'
                        self.reason = 'wol log find error\warning please check'
                        return self.result, self.reason
                    else:
                        continue
            else:
                self.result = 'fail'
                self.reason = 'get log file error check log file if exist'
                return self.result, self.reason
            time.sleep(10)
        return self.result, self.reason
        
def powerstate_check():
    '''
    description: this function is check remote server chassis status
    '''
    global serverstate
    global BMCIP
    global user
    global password
    ipmicount = 1
    while ipmicount <= 3:
        powerret, powerres = subprocess.getstatusoutput("ipmitool -H %s -I lanplus -U %s -P %s chassis status" % (BMCIP, bmcuser, bmcpassword))
        if powerret != 0 or powerres == '':
            logger.info("the server_power_state check ipmi command perform fail and try 3 times")
        else:
            break
        time.sleep(20)
        ipmicount = ipmicount + 1             
    if ipmicount == 3 and powerres == '':
        logger.error("the server_power_state check ipmi command perform error")   
        exit()        
    for syskey in powerres.split('\n'):
        if "System Power" in syskey:
            powerstate = syskey
    if powerstate.split(":")[1].strip() == "on":
        serverstate = "on"
    elif powerstate.split(":")[1].strip() == "off":
        serverstate = "off"
    else:
        logger.error("get system power error")
        exit()

def ping_nin(ip):
    '''
        description: ping hardware
        author: yuhanhou
        params: ip, the IP address of hardware
                kwargs, ping options
                    max_time: if can'\t ping, retry ping during the max_time duration after wait delay time
                    delay_time: default is 10s, wait for time before next ping
                    retry_time: default is 3, retry time for the ping if failed. don't use this param with max_time together
        return: ping result, True/False/percentage of package loss when networking issue.
    '''
    ping_count = 1
    while True:
        cmd_out = subprocess.getstatusoutput("ping -c 3 %s" % ip)
        ping_count += 1
        cmd_out = str(cmd_out)
        if re.search('100% packet loss', cmd_out, re.I):
            logger.error("host " + ip + " is not available!")
            return False
        elif re.search(r'.*\s0% packet loss', cmd_out, re.I):
            logger.info("network of " + ip + " is ok.")
            return True
        elif re.search(r'(.*\s[3-6][3-6]% packet loss)', cmd_out, re.I):
            if ping_count > 3:
                logger.warn(ip + " has networking issue. Please check it!")
                m = re.search(r'(.*\s[3-6][3-6]% packet loss)', cmd_out, re.I)
                return m.group(0)
            else:
                continue

def power_off():
    '''
    description: this function is shoutdown remote server
    '''
    global ospassword
    global osuser
    global NICIP
    os.system("sshpass -p %s ssh -o StrictHostKeyChecking=no %s@%s init 0" % (ospassword, osuser, NICIP))
    time.sleep(100)
    powerstate_check()
    if serverstate == "off":
        logger.info("server is shutdown")
        return True
    else:
        pass
        logger.error("server shutdown error")
        return False

def power_on():
    '''
    description: this function is use wol command start server
    '''
    global serverstate
    wol_onret, wol_onres = subprocess.getstatusoutput("wol -h %s %s" % (host,mac))
    if wol_onret != 0 or wol_onres == '':
        logger.error("cmd wol send to server error")
        return False
    time.sleep(100)
    powerstate_check()
    if serverstate == 'on':
        logger.info("wol cmd excute successful")
        return True
    else:
        logger.error("The wol cmd is send but server power state is off")
        return False

def exit_c(signum, frame):
    print('You choose to stop')
    exit()
signal.signal(signal.SIGINT, exit_c)
signal.signal(signal.SIGTERM, exit_c)

if __name__ == '__main__':
    logcheck = Test_wol_check(logfile=logger.log_file)
    logthread = MyThread(logcheck.log_check)
    logthread.start()
    print("start wol on cycle test")
    while powercount < xconunts:
        powerstate_check()
        if serverstate == "on":
            time.sleep(300)
            powercount += 1
            logger.info("normal poweron count : %s" % powercount)
        else:
            logger.error("server power state is off")
            break
        pingstate = ping_nin(NICIP)
        if pingstate == True:
            pf = power_off()
            if pf == False:
                break
            po = power_on()
            if po == False:
                break
        else:
            break
    time.sleep(20)
    logger.info("wol cycle test done")
    logthread.join()
    print(logthread.get_result()) 