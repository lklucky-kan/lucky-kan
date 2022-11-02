import re
import os
import sys
import shutil
import subprocess

class Disk_Check():
    
    def __init__(self,state=None,onlycollect=False,key=None):
        self.state = ''
        if state == None:
            self.state = 'disk_info'
        else:
            self.state = state #before or after
        self.logdir = 'reports'
        self.diskdir = "%s/diskinfo/%s" % (self.logdir,self.state)
        if not os.path.isdir(self.logdir):
            self.logdir = '.'
        if os.path.exists("%s/diskinfo/smartcheck_success.log" % self.logdir):
            os.remove("%s/diskinfo/smartcheck_success.log" % self.logdir)
        if os.path.exists("%s/diskinfo/smartcheck_fail.log" % self.logdir):
            os.remove("%s/diskinfo/smartcheck_fail.log" % self.logdir)
        disk_tmp = subprocess.getstatusoutput("lsblk |grep -i disk |awk '{print $1}'")[1].split('\n')
        self.hddlist = []
        self.nvmelist = []
        self.keys = key
        for disk in disk_tmp:
            if re.search(r'sd\S$',disk,re.I):
                self.hddlist.append(disk)
            elif re.search(r'nvme\dn\d$',disk,re.I):
                self.nvmelist.append(disk)

    def smartlog_save(self):
        if not os.path.exists(self.diskdir):
            os.makedirs(self.diskdir)
        else:
            shutil.rmtree(self.diskdir)
            os.makedirs(self.diskdir)        
        if self.hddlist:
            for hdd in self.hddlist:
                subprocess.getstatusoutput('smartctl -a /dev/%s >%s/%s.log' % (hdd,self.diskdir,hdd))
        else:
            with open("%s/diskinfo.log" % self.diskdir , 'w') as f:
                f.write("No HDD need check")
                f.write('\n')
        if self.nvmelist:
            for nvme in self.nvmelist:
                subprocess.getstatusoutput('smartctl -a /dev/%s >%s/%s.log' % (nvme,self.diskdir,nvme))
        else:
            with open("%s/diskinfo.log" % self.diskdir , 'w') as f:
                f.write("No NVME need check")
                f.write('\n')            
    
    def is_ssd_or_sata(self,dev):
        checktmp = subprocess.getstatusoutput("smartctl -a /dev/%s |grep -i 'Rotation Rate'" % dev)[1].split(":")[-1].strip()
        if checktmp == 'Solid State Device':
            return 1
        else:
            return 0

    def save_checklog(self,state,msg):
        with open("%s/diskinfo/smartcheck_%s.log" % (self.logdir,state),"a") as f:
            f.write(msg)
            f.write('\n')

    def smartlog_check(self):
        errmsg = []
        checkflag = True
        if not self.hddlist and not self.nvmelist:
            errmsg.append("No Disk need check")
            return checkflag,errmsg
        if self.hddlist:
            for hddtmp in self.hddlist:
                if self.is_ssd_or_sata(dev=hddtmp):
                    hddblack_l = self.keys['SSD']['black_list']
                else:
                    hddblack_l = self.keys['SATA']['black_list']
                for bkey in hddblack_l:
                    if os.path.exists('%s/diskinfo/after/%s.log' % (self.logdir,hddtmp)) and os.path.exists('%s/diskinfo/before/%s.log' % (self.logdir,hddtmp)):
                        hafinfo = subprocess.getstatusoutput('cat %s/diskinfo/after/%s.log |grep -i "%s"|head -n1' % (self.logdir,hddtmp,bkey))[1]
                        hbeinfo = subprocess.getstatusoutput('cat %s/diskinfo/before/%s.log |grep -i "%s"|head -n1' % (self.logdir,hddtmp,bkey))[1]
                        if hafinfo != hbeinfo:
                            errmsg.append("Check smart info fail in %s before: %s ; after %s" % (hddtmp,hbeinfo,hafinfo))
                            checkflag = False
                            info = "Check smart info fail in %s before: %s ; after %s" % (hddtmp,hbeinfo,hafinfo)
                            self.save_checklog(state='fail',msg=info)
                        else:
                            if hafinfo != '' and hbeinfo != '':
                                info = "Check %s Smart Info Success Before : %s After : %s" % (hddtmp,hbeinfo,hafinfo)
                                self.save_checklog(state='success',msg=info)
                    else:
                        errmsg.append("Not Find Smart Log in %s/diskinfo please check if %s.log in before dir or after dir" % (self.logdir,hddtmp))
                        checkflag = False
                        info = "Not Find Smart Log in %s/diskinfo please check if %s.log in before dir or after dir" % (self.logdir,hddtmp)
                        self.save_checklog(state='fail',msg=info)
        if self.nvmelist:
            nvmeblack_l = self.keys['NVME']['black_list']
            for nvmetmp in self.nvmelist:
                for nkey in nvmeblack_l:
                    if os.path.exists('%s/diskinfo/after/%s.log' % (self.logdir,nvmetmp)) and os.path.exists('%s/diskinfo/before/%s.log' % (self.logdir,nvmetmp)):
                        nafinfo = subprocess.getstatusoutput('cat %s/diskinfo/after/%s.log |grep -i "%s"|head -n1' % (self.logdir,nvmetmp,nkey))[1]
                        nbeinfo = subprocess.getstatusoutput('cat %s/diskinfo/before/%s.log |grep -i "%s"|head -n1' % (self.logdir,nvmetmp,nkey))[1]
                        if nafinfo != nbeinfo:
                            errmsg.append("Check smart info fail in %s before: %s ; after %s" % (nvmetmp,nbeinfo,nafinfo))
                            checkflag = False
                            info = "Check smart info fail in %s before: %s ; after %s" % (nvmetmp,nbeinfo,nafinfo)
                            self.save_checklog(state='fail',msg=info)
                        else:    
                            if nafinfo != '' and nbeinfo != '':
                                info = "Check %s Smart Info Success Before : %s After : %s" % (nvmetmp,nbeinfo,nafinfo)
                                self.save_checklog(state='success',msg=info)          
                    else:
                        errmsg.append("Not Find Smart Log in %s/diskinfo please check if %s.log in before dir or after dir" % (self.logdir,nvmetmp))
                        checkflag = False
                        info = "Not Find Smart Log in %s/diskinfo please check if %s.log in before dir or after dir" % (self.logdir,nvmetmp)
                        self.save_checklog(state='fail',msg=info)
        return checkflag, errmsg

if __name__ == '__main__':
    disk_chk = Disk_Check()
    