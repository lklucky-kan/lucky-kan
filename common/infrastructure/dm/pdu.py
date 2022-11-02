from re import I


import re
from common.infrastructure.hardware import Hardware
from common.communication.ssh import SSH
class PDU(Hardware):
    '''
    description: currently use APC pdu.
    '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user = kwargs.get('user', 'apc')
        self.password = kwargs.get('password', 'apc')
        self.ip = kwargs.get('ip')
        self.prompt = self.user + '>'

        self.session = SSH(user=self.user, password=self.password, ip=self.ip, prompt=self.prompt, logger=self.logger)


    def power_on(self, *ports, **kwargs):
        '''
        description: power on the port of port group with or without delay
        author: yuhanhou
        params: ports, unpacking ports list to power on
                kwargs, optional params
                    delay:10  #set the delay of the power on,unit is second
        return:
        '''
        delay = kwargs.get('delay', 0)
        out = ''

        if delay:
            out = self.session.cmd('olOn ' + ','.join(ports), return_list=False)
        else:
            self.set_power_on_delay(delay, *ports)
            out = self.session.cmd('olDlyOn ' + ','.join(ports), return_list=False)

        if re.search('success', out, re.I):
            return True
        else:
            return False

    def power_off(self, *ports, **kwargs):
        '''
        description: power off the port of port group with or without delay
        author: yuhanhou
        params: ports, unpacking ports list to power off
                kwargs, optional params
                    delay:10  #set the delay of the power off,unit is second
        return:
        '''        
        delay = kwargs.get('delay', 0)
        out = ''

        if delay:
            out = self.session.cmd('olOff ' + ','.join(ports), return_list=False)
        else:
            self.set_power_off_delay(delay, *ports)
            out = self.session.cmd('olDlyOff ' + ','.join(ports), return_list=False)

        if re.search('success', out, re.I):
            return True
        else:
            return False


 


    def power_cycle(self, *ports, **kwargs):
        '''
        description: power cycle the port of port group with or without delay
        author: yuhanhou
        params: ports, unpacking ports list to power cycle
                kwargs, optional params
                    delay:10  #set the reboot duration of the power cycle,unit is second
                    off_delay:5  #power off delay 
                    on_delay: 5   #power_on_delay, the total delay between off and on should be delay+on_delay
        return:
        '''           
        delay = kwargs.get('delay', 0)
        off_delay = kwargs.get('off_delay', 0)
        on_delay = kwargs.get('on_delay', 0)
        out = ''

        self.set_reboot_delay(delay, *ports)
        self.set_power_off_delay(off_delay, *ports)
        self.set_power_on_delay(on_delay, *ports)

        out = self.session.cmd('olReboot ' + ','.join(ports), return_list=False)

        if re.search('success', out, re.I):
            return True
        else:
            return False


    def set_power_on_delay(self, delay, *ports):
        '''
        description: set power on delay for ports
        author: yuhanhou
        params: delay:10  #set the delay of the power on,unit is second
                ports, unpacking ports list to set
                 
                    
        return:
        '''           
        out = ''

        out = self.session.cmd('olOffDelay ' + ','.join(ports) + ' ' + str(delay), return_list=False)
        
        if re.search('success', out, re.I):
            return True
        else:
            return False


    def set_power_off_delay(self, delay, *ports):
        '''
        description: set power off delay for ports
        author: yuhanhou
        params: delay:10  #set the delay of the power off,unit is second
                ports, unpacking ports list to set
                 
                    
        return:
        '''           
        out = ''

        out = self.session.cmd('olOnDelay ' + ','.join(ports) + ' ' + str(delay), return_list=False)
        
        if re.search('success', out, re.I):
            return True
        else:
            return False


    def set_reboot_delay(self, delay, *ports):
        '''
        description: set power cycle delay for ports
        author: yuhanhou
        params: delay:10  #set the delay of the power cycle ,unit is second
                ports, unpacking ports list to set
                 
                    
        return:
        '''           
        out = ''

        out = self.session.cmd('olRbootTime ' + ','.join(ports) + ' ' + str(delay), return_list=False)
        
        if re.search('success', out, re.I):
            return True
        else:
            return False

 