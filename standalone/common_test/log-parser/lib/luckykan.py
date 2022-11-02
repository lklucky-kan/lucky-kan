import subprocess
import os,sys,time

# 获取本地路径
path = os.path.dirname(os.path.realpath(__file__))
# log_path是存放日志的路径
log_path = os.path.join(path, '../reports')
# 如果不存在这个logs文件夹，就自动创建一个
if not os.path.exists(log_path):
    os.mkdir(log_path)
os.path.join(log_path, './raid.log')

class RaidErrorRateCheck(object):
    def __init__(self) -> None:
        self.nic_port = []
        self.logname = os.path.join(log_path, './raid.log')

    def get_raid_log(self):
        pass     
        # raid_log = subprocess.getstatusoutput("storcli64 /call/pall show all")[1].split("\n")
        
        # nic_devices = subprocess.getstatusoutput("ls -l /sys/class/net/ | grep %s |awk -F ' ' '{print $9F}'"% businfo)[1].split("\n")
        # self.nic_port.append(nic_devices)
        # nic_driver_load_list = ['sssudk','sssdk','sssnic']
        # for nic_driver_load in nic_driver_load_list:
        #     subprocess.getstatusoutput("modprobe %s"% nic_driver_load)
        # print(self.nic_port[0])

if __name__== '__main__':
    ss = RaidErrorRateCheck()
    ss.get_raid_log()