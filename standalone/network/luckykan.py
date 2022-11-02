from lib2to3.pgen2 import driver
import subprocess
class d:
    def __init__(self) -> None:
        self.nic_port = []
    def fun(self):
                
        businfo_list = subprocess.getstatusoutput("lspci |grep -i ' Ethernet controller'| awk -F ' ' '{print $1F}'")[1].split("\n")

        for businfo in businfo_list:
            nic_devices = subprocess.getstatusoutput("ls -l /sys/class/net/ | grep %s |awk -F ' ' '{print $9F}'"% businfo)[1].split("\n")
            self.nic_port.append(nic_devices)
        nic_driver_load_list = ['sssudk','sssdk','sssnic']
        for nic_driver_load in nic_driver_load_list:
            subprocess.getstatusoutput("modprobe %s"% nic_driver_load)
        print(self.nic_port[0])

if __name__== '__main__':
    ss = d()
    ss.fun()