import subprocess
import os
import sys
import argparse
import math
import re
import time
import shutil

tea_path = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.pardir,
        os.pardir
        )
)
sys.path.append(tea_path)

pars = argparse.ArgumentParser()
pars.description = "python3 memory_cycle.py -c xx -w dc/reboot -t memtester/stressapptest"
pars.add_argument("-c", "--count",required=False,default='none',help="please input test count")
pars.add_argument("-w", "--testway", required=False,default="reboot",help="input cycle way default reboot -w dc/reboot")
pars.add_argument("-t", "--memtool",required=False,default="memtester",help="input memory stress tool,default tool :memtester")
argspart = vars(pars.parse_args())

if re.search(r'%s' % os.path.abspath('.'), os.path.dirname(__file__), re.I):
    baselocallogpath = os.path.dirname(__file__)
else:
    if os.path.dirname(__file__).split('/')[0] != '':
        baselocallogpath = os.path.abspath('.') + "/" + os.path.dirname(__file__)
    else:
        baselocallogpath = os.path.abspath('.') + os.path.dirname(__file__)
scriptdir = baselocallogpath
baselocallogpath = baselocallogpath + '/' + 'result/memory_cycle/'
if not os.path.exists(baselocallogpath):
    os.system('mkdir -p %s' % baselocallogpath)

class Mem_stress_cycle():
    '''
    author :wanglei
    description :class init ,init log path ,script path, get test memory size,
    params : count   :memory stress cycle count
             testway :select cycle way reboot or ipmitool power cycle
    '''
    def __init__(self,count,testway,memtool):
        self.count =  count
        self.testway = testway
        self.memtool = memtool
        self.teapth = scriptdir.split('standalone')[0]
        self.testmemsize = math.ceil(int(subprocess.getstatusoutput("free -m | grep Mem | awk '{print $2}'")[1]) * 0.9)
        self.cycle_count_path = os.path.join('/root/', 'memory' + '_cycle' + '.txt')
        self.check_memory_path = os.path.join('/root/', 'memory' + '_check' + '.log')
        os.system("chmod -R 777 %s &>/dev/zero" % self.cycle_count_path)
        os.system("chmod -R 777 %s &>/dev/zero" % self.check_memory_path)
        self.log_filter_path = scriptdir.split('standalone')[0] + 'standalone/common_test/log-parser/'
        self.sys_log_path = baselocallogpath + "sys_log"
        if self.count != 'none':
            os.system("rm -rf %s" % self.cycle_count_path)
            os.system("rm -rf %s" % self.check_memory_path)
            os.system("rm -rf /root/memory_cycle_error.log")
            shutil.rmtree(baselocallogpath)
            self.log_handle(act='clear')
        if not os.path.exists(self.sys_log_path):
            os.makedirs(self.sys_log_path)       

    def log_handle(self,act,testcount=None):
        if act == 'clear':
            subprocess.getstatusoutput('python3 %slog_parser.py --b' % self.log_filter_path)
        elif act == 'save':
            subprocess.getstatusoutput('python3 %slog_parser.py --a' % self.log_filter_path)
            os.system('cp -rf %sreports %s/report_count%s' % (self.log_filter_path,self.sys_log_path,testcount))

    def save_dimm_info(self):
        '''
        author :wanglei
        description :save dimm info in testing,include memory total memory used memory percent
        return : percent accord percent select if reboot/ipmitool power cycle
        '''
        before_wc = subprocess.getstatusoutput("cat %s |wc -l" % self.check_memory_path)[1]
        while True:
            memtotalmb = int(subprocess.getstatusoutput("free -m | grep Mem | awk '{print $2}'")[1])
            memfreemb = int(subprocess.getstatusoutput("free -m | grep Mem | awk '{print $4}'")[1])
            memusemb = int(memtotalmb) - int(memfreemb)
            percent = int((memusemb*100)/memtotalmb)
            with open(self.check_memory_path,'a') as f:
                meminfo = []
                meminfo.append("MemTotalMB :%s MemTotalGB :%s" % (memtotalmb,math.ceil(memtotalmb/1024)))
                meminfo.append("MemUsedMB  :%s MemUsedGB  :%s" % (memusemb,math.ceil(memusemb/1024)))
                meminfo.append("The Percent of Used memory is about %s" % percent)
                for memtmp in meminfo:
                    f.write(memtmp)
                    f.write('\n')
                f.write('\n')
            after_wc = subprocess.getstatusoutput("cat %s |wc -l" % self.check_memory_path)[1]
            if int(after_wc) > int(before_wc) :
                break
            else:
                time.sleep(2)
        return percent

    def get_count(self):
        '''
        author :wanglel
        description :get memory stress cycle test counts.
        return :if first run return 0,else return current counts
        '''
        count = subprocess.getstatusoutput("cat %s" % self.cycle_count_path)
        if count[0] != 0 or re.search(r'No such file or directory',count[1],re.I):
            cycle = 0
        else:
            cycle = eval(count[1])['current_count']
        return cycle

    def write_count(self,count,info):
        info['current_count'] = count
        with open(self.cycle_count_path,'w') as f:
            f.write(str(info))

    def clean_rclocal(self):
        '''
        description :before test and after test clean /etc/rc.d/rc.local
        '''
        os.system("sed -i '/python/d' /etc/rc.d/rc.local")
        #os.system("sed -i '/tea/d' /etc/rc.d/rc.local")

    def check_ipmitool(self):
        check_count = 0
        while True:
            check_count = check_count + 1
            cmdres1 = subprocess.getstatusoutput('command -v ipmitool')[1]
            cmdres2 = subprocess.getstatusoutput('ipmitool')[1]
            if cmdres1 != '' and not re.search(r'Could not open device',cmdres2,re.I):
                return True
            else:
                if check_count > 3:
                    return False
            time.sleep(3)

    def check_memtool_exist(self):
        check_tool_res = subprocess.getstatusoutput('command -v %s' % self.memtool)[1]
        if check_tool_res == '':
            sys.exit("%s not find please check" % self.memtool)

    def mem_stress(self,memact):
        '''
        author :wanglei
        description :start memory stress test or clear memory stress
        params :memact test/clear
        '''
        if memact == 'test':
            while True:
                old_stress = subprocess.getstatusoutput('ps -e |grep -i %s' % self.memtool)[1]
                if old_stress:
                    os.system("killall %s &>/dev/zero" % self.memtool)
                    time.sleep(2)
                else:
                    break
            if self.memtool == 'memtester':
                os.system("memtester %s >/dev/zero &" % self.testmemsize)
            elif self.memtool == 'stressapptest':
                os.system("stressapptest -M %s -s 300 >/dev/zero &" % self.testmemsize)
        elif memact == 'clear':
            while True:
                old_stress = subprocess.getstatusoutput('ps -e |grep -i %s' % self.memtool)[1]
                if old_stress:
                    os.system("killall %s &>/dev/zero" % self.memtool)
                    time.sleep(2)
                else:
                    break

    def first_run_cycle(self):
        '''
        author :wanglei
        description :add test command into /etc/rc.d/rc.local and create test count txt
        '''
        self.clean_rclocal()
        savecycle = {}
        with open(self.cycle_count_path,'w') as f:
            savecycle['current_count'] = 1
            savecycle['total_count'] = self.count
            f.write(str(savecycle))
        os.system("chmod -R 777 /etc/rc.d/rc.local")
        cmd = "python3 %s/memory_cycle.py -w %s -t %s" % (scriptdir,self.testway,self.memtool)
        with open('/etc/rc.d/rc.local','a') as f:
            f.write(cmd)
            f.write('\n')

    def run(self):
        '''
        author :wanglei
        description :class run method
        '''
        self.check_memtool_exist()
        check_flag = True
        testcycle = self.get_count()
        if testcycle == 0:
            check_flag = False
            testcycle = testcycle + 1
            self.first_run_cycle()
        countinfotmp = subprocess.getstatusoutput("cat %s" % self.cycle_count_path)[1]
        countinfo = eval(countinfotmp)
        if int(countinfo['current_count']) < int(countinfo['total_count']):
            new_cycleinfo = "test cycle count" + " " + str(testcycle)
            if check_flag:
                last_info_tmp = subprocess.getstatusoutput("cat %s |grep -i 'test cycle count' |tail -n1" % self.check_memory_path)[1]
                check_if_over = subprocess.getstatusoutput("cat %s |grep -i 'The Percent of Used memory is about' |tail -n1" % self.check_memory_path)[1]
                if re.search(r'\d+',last_info_tmp,re.I):
                    last_count = re.search(r'\d+',last_info_tmp,re.I).group(0)
                else:
                    last_count = 0
                if re.search(r'\d+',check_if_over,re.I):
                    memstress_value = re.search(r'\d+',check_if_over,re.I).group(0)
                else:
                    memstress_value = 0
                if int(last_count) == int(testcycle) and int(memstress_value) > 89:
                    testcycle = testcycle + 1
                    self.write_count(count=testcycle,info=countinfo)
                else:
                    os.system("sed -i '/%s/,$d' %s" % (new_cycleinfo,self.check_memory_path))
            os.system("echo '##################test cycle count %s##################' >>%s" % (testcycle,self.check_memory_path))
            self.log_handle(act="save",testcount=testcycle)
            self.log_handle(act='clear')
            self.mem_stress(memact='test')
            sleep_count = 0
            while True:
                currentpercent = self.save_dimm_info()
                if currentpercent > 89:
                    self.mem_stress(memact='clear')
                    time.sleep(20)
                    if self.testway == 'dc':
                        if self.check_ipmitool():
                            print('dc cycle')
                            if check_flag:
                                print('ipmitool raw 0 2 2')
                                subprocess.getstatusoutput('ipmitool raw 0 2 2')
                            else:
                                print('reboot')
                                subprocess.getstatusoutput('reboot')
                            time.sleep(10)
                        else:
                            os.system('echo "ipmitool not install or can not use" >/root/memory_cycle_error.log')
                            os.system('cp -rf /root/memory_cycle_error.log %s &>/dev/zero' % baselocallogpath)
                            self.clean_rclocal()
                            sys.exit("ipmitool not install or can not use")
                    elif self.testway == 'reboot':
                        print('reboot')
                        subprocess.getstatusoutput('reboot')
                        time.sleep(10)
                else:
                    sleep_count = sleep_count + 1
                    time.sleep(3)
                    if sleep_count > 100:
                        os.system('echo "memory stress not greater than 90 please check" >/root/memory_cycle_error.log')
                        os.system('cp -rf /root/memory_cycle_error.log %s &>/dev/zero' % baselocallogpath)
                        self.clean_rclocal()
                        sys.exit("memory stress not greater than 90 please check")
                time.sleep(10)
        else:
            os.system("echo '##################test cycle end##################' >>%s" % self.check_memory_path)
            os.system('cp -rf %s %s' % (self.cycle_count_path,baselocallogpath))
            os.system('cp -rf %s %s' % (self.check_memory_path,baselocallogpath))
            self.clean_rclocal()
            sys.exit("test cycle end")
if __name__ == '__main__':
    memobj = Mem_stress_cycle(count=argspart['count'],testway=argspart['testway'],memtool=argspart['memtool'])
    memobj.run()
