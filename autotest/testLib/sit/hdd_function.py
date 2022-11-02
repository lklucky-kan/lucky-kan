import os
import subprocess
import re
import time
import copy
from autotest.testLib.base import Base
from common.other.log import Logger
from common.file.json_rw import fopen

class Hdd_function(Base):

    def __init__(self,**kwargs):
        '''
        author: wanglei
        description: this class use to test HDD link reset
        params: testcount : hdd linkreset cycle counts
                recover   : use to recover hdd (if Hard disk unrecognized in interrupt test)
        '''        
        Base.__init__(self, **kwargs)
        '''
        author: wanglei
        description: class init mathod,find os hdd(os hdd do not test),create key-value {'sda':'busid',......},save current hdd info,
                     create log to save test result
        '''
        self.result = {}
        osdevicetmp = subprocess.getstatusoutput('lsblk |grep -i /boot$')[1]
        self.osdevice = re.search(r'sd\S', osdevicetmp, re.I).group(0)
        self.bus_name = {}
        bus_nametmpb = subprocess.getstatusoutput("lsscsi |sort -k 6 |grep -i disk |grep -ivE '%s|nvme'" % self.osdevice)[1].split('\n')
        self.initdiskc = len(bus_nametmpb)
        for sn in copy.deepcopy(bus_nametmpb):
            if sn == '':
                bus_nametmpb.remove(sn)
        if bus_nametmpb:
            for bntmp in bus_nametmpb:
                bus = re.search(r'\w+:\w+:\w+:\w+',bntmp,re.I).group(0)
                nametmp = re.search(r'/dev/sd\S',bntmp,re.I).group(0)
                name = nametmp.split('/')[-1]
                if re.search(r'INTEL',bntmp,re.I):
                    name = name + "-" + "INTEL"
                else:
                    name = name + "-" + "HDD"
                self.bus_name[name] = bus
            self.hddcount = len(self.bus_name)
        print(self.bus_name)
        if not os.path.exists('/%s/%s' % ('root','hdd_infomation')):
            f = open("/%s/%s" % ('root','hdd_infomation'),'a')
            f.write(str(self.bus_name))
            f.close()
        self.testcount = kwargs.get('testcount')
        self.recoverflag = kwargs.get('recover')
        self.reset_log_file = os.path.join(self.log_path, self.testcase + '_other' + '.log')
        self.reset_checklog_file = os.path.join(self.log_path, self.testcase + '_check' + '.log')
        self.reset_debug_file = os.path.join(self.log_path, self.testcase + '_debug' + '.log')
        self.resetlogger = Logger(log_file=self.reset_log_file,log_file_timestamp=False,stdoutput=False)
        self.resetchecklogger = Logger(log_file=self.reset_checklog_file,log_file_timestamp=False,stdoutput=False)
        self.resetdebuglogger = Logger(log_file=self.reset_debug_file,log_file_timestamp=False,stdoutput=False)

    def reset_function(self,devicename,busname,act):
        '''
        author : wanglei
        description :According to the act(delete or recover) to delete hdd or recover hdd
        params: devicename :hdd name space sdb sdc ......
                busname :x:x:x:x
                act :delete or recover
        '''
        if act == 'delete':
            self.resetlogger.info('echo 1 > /sys/block/%s/device/delete' % devicename)
            os.system('echo 1 > /sys/block/%s/device/delete' % devicename)
        elif act == 'recover':
            recoverbus = busname.split(':')[0]
            self.resetlogger.info('echo "- - -" > /sys/class/scsi_host/host%s/scan' % recoverbus)
            os.system('echo "- - -" > /sys/class/scsi_host/host%s/scan' % recoverbus)

    def log_check(self,teststatus):
        '''
        author :wanglei
        description :check dmesg messages sel log ,if find the key word return fail
        params :teststatus :before or after,before means before test check log,after means after test check log 
        '''
        os.system("ipmitool sel list > %s/%s_sel.log" % (self.log_path,teststatus))
        os.system("cat /var/log/messages > %s/%s_messages.log" % (self.log_path,teststatus))
        os.system("dmesg > %s/%s_dmesg.log" % (self.log_path,teststatus))
        os.system('if [[ ! -d %s/%s ]]; then mkdir %s/%s; fi' % (self.log_path,teststatus,self.log_path,teststatus))
        for namek in self.bus_name.keys():
            os.system("smartctl -a /dev/%s >>%s/%s/%s_smart_log" % (namek.split('-')[0],self.log_path,teststatus,namek.split('-')[0]))
        
        data = fopen(file='standalone/common_test/log-parser/data/black_white.json',json=True)
        bmcblack = data['bmc']['black_list']
        dmesgblack = data['dmesg']['black_list']
        messagesblack = data['messages']['black_list']
        
        bmclog = subprocess.getstatusoutput("cat %s/%s_sel.log" % (self.log_path,teststatus))[1]
        for bmctmp in bmcblack:
            if bmctmp.lower() in bmclog.lower():
                self.result['result'] = "fail"
                self.result['reason'] += "find error %s in %s/%s_sel.log please check" % (bmctmp,self.log_path,teststatus)
        
        dmesglog = subprocess.getstatusoutput("cat %s/%s_dmesg.log" % (self.log_path,teststatus))[1]
        for dmesgtmp in dmesgblack:
            if re.search(r'\s+%s' % dmesgtmp,dmesglog,re.I):
                self.result['result'] = "fail"
                self.result['reason'] += "find error %s in %s/%s_dmesg.log please check" % (dmesgtmp,self.log_path,teststatus)

        messageslog = subprocess.getstatusoutput("cat %s/%s_messages.log" % (self.log_path,teststatus))[1]
        for messagestmp in messagesblack:
            if re.search(r'\s+%s' % messagestmp,messageslog,re.I):
                self.result['result'] = "fail"
                self.result['reason'] += "find error %s in %s/%s_messages.log " % (messagestmp,self.log_path,teststatus)

    def hdd_log_check(self):
        '''
        author :wanglei
        description :check smart log if find the key word has change return error.
        '''
        for hddname in self.bus_name.keys():
            if hddname.split('-')[1] == 'INTEL':
                hdd_checklist = ['Reallocated_Sector_Ct','End-to-End_Error_Count','Pending_Sector_Count','CRC_Error_Count']
            else:
                hdd_checklist = ['Reallocated_Sector_Ct','Reported_Uncorrect','Current_Pending_Sector','Offline_Uncorrectable','UDMA_CRC_Error_Count']
            for hdditem in hdd_checklist:
                afteritem = subprocess.getstatusoutput('cat %s/after/%s_smart_log |grep -i %s' % (self.log_path,hddname.split('-')[0],hdditem))[1]
                beforitem = subprocess.getstatusoutput('cat %s/before/%s_smart_log |grep -i %s' % (self.log_path,hddname.split('-')[0],hdditem))[1]
                if afteritem != beforitem:
                    self.resetchecklogger.error('check hdd smart info error fail item: %s on hdd %s' % (afteritem.split(' ')[1],hddname.split('-')[0]))
                    self.result['result'] = "fail"
                    self.result['reason'] = "check hdd smart info fail please check log %s" % self.reset_checklog_file
                else:
                    keyindex = 0
                    keytmp = afteritem.split(' ')
                    for k in keytmp:
                        if k != '':
                            keyindex = keytmp.index(k)
                            break
                    self.resetchecklogger.info('check hdd smart info pass item: %s on hdd %s' % (keytmp[keyindex+1],hddname.split('-')[0]))

    def test_linkreset(self):
        '''
        author :wanglei
        description :test way for hdd link reset,if test pass return pass else return fail
        '''
        if self.bus_name:
            self.result['result'] = "pass"
            self.result['reason'] = ""
            if self.recoverflag != 'True':
                self.log_check(teststatus='before')
                for testc in range(1,int(self.testcount)+1):
                    checkcount = 1
                    print('##########test hdd linkreset cycle : %s##########' % testc)
                    self.resetlogger.info('##########test hdd linkreset cycle : %s##########' % testc)
                    self.resetdebuglogger.info('##########test hdd linkreset cycle : %s##########' % testc)
                    for dk,dv in self.bus_name.items():
                        self.reset_function(devicename=dk.split('-')[0],busname=dv,act='delete')
                    time.sleep(8)
                    for rk,rv in self.bus_name.items():
                        self.reset_function(devicename=rk.split('-')[0],busname=rv,act='recover')
                    while True:
                        time.sleep(10)
                        bus_name = {}
                        bus_nametmpa = subprocess.getstatusoutput("lsscsi |sort -k 6 |grep -i disk |grep -ivE '%s|nvme'" % self.osdevice)[1].split('\n')
                        checkdiskc = len(bus_nametmpa)
                        print("current disk counts %s" % checkdiskc)
                        print(" init   disk counts %s" % self.initdiskc)
                        if int(checkdiskc) != int(self.initdiskc):
                            print("the current disk counts != init disk counts sleep 10S and try")
                            time.sleep(10)
                            continue
                        for bntmp in bus_nametmpa:
                            self.resetdebuglogger.info(bntmp)
                            cbustmp = re.search(r'\w+:\w+:\w+:\w+',bntmp,re.I)
                            if cbustmp != '':
                                cbus = re.search(r'\w+:\w+:\w+:\w+',bntmp,re.I).group(0)
                            else:
                                cbus = ''
                            cnametmp1 = re.search(r'/dev/sd\S',bntmp,re.I)
                            if cnametmp1 != '' and '/dev/sd' in bntmp:
                                try:
                                    cnametmp = re.search(r'/dev/sd\S',bntmp,re.I).group(0)
                                except AttributeError:
                                    cnametmp = subprocess.getstatusoutput("echo %s |awk '{print$NF}'" % bntmp)[1]
                            else:
                                cnametmp = ''
                            cname = cnametmp.split('/')[-1]
                            if cname != '' and cbus != '':
                                bus_name[cname] = cbus
                        if len(bus_name) == self.hddcount:
                            break
                        elif checkcount > 3:
                            print(bus_name)
                            self.result['result'] = 'fail'
                            self.result['reason'] = 'hdd count has change check'
                            return self.result
                        time.sleep(3)
                        checkcount = checkcount + 1

                    for checkk in self.bus_name.keys():
                        if self.bus_name[checkk] != bus_name[checkk.split('-')[0]]:
                            self.resetlogger.error("recover error num %s" % testc)
                            self.result['result'] = 'fail'
                            self.result['reason'] = 'fail recover cycle %s and fail hdd : %s' % (testc,checkk.split('-')[0])
                            return self.result
                    time.sleep(3)
                self.log_check(teststatus='after')
                self.hdd_log_check()
            else:
                bakhdd = subprocess.getstatusoutput('cat /%s/%s' % ('root','hdd_infomation'))[1]
                for retmpk,retmpv in eval(bakhdd).items():
                    self.reset_function(devicename=retmpk.split('-')[0],busname=retmpv,act='recover')
        else:
            self.result['result'] = 'fail'
            self.result['reason'] = 'No HDD can do link reset test'
        return self.result
