import re
import time
from autotest.testLib.base import Base
from common.infrastructure.dm.pdu import PDU
from common.infrastructure.sm.bmc import BMC


class BMCTest(Base):
    '''
    description: this class is test library for bmc feature
    author: yuhanhou
    '''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    
    def test_chassis_always_off(self):
        '''
        description: test for bmc chassis  always-off policy, pdu is required for this case
                     tp-5401 : SERV-STFT-BMC-0005_Restore on AC Power Loss-Power off 	
        author: yuhanhou
        params: NA
        return: result, dict of 
                {
                    'result': 'pass|fail'
                    'reason': 'some_fail_reason'
                }
        '''
        #get bmc info:
        server_info = self.options.get('server') 
        server_obj = self.get_obj(server_info.get('ip'))
        self.logger.info('set always-off policy on DUT...')
        server_obj.cmd('ipmitool chassis policy always-off')


        #bmc obj create:
        bmc_ip = server_info.get('bmc_ip')        
        bmc_obj = self.get_obj(bmc_ip)


        power_cycle_times = int(self.options.get('testcase').get('cycle', 4)) #the last time need shutdown OS first before AC power cycle
        #check server's power status before test:
        output = bmc_obj.cmd('chassis power status', return_list=False)
        if not re.search('Chassis Power is on', output, re.I):
            self.logger.error('Server is off which is not ready for this test!')
            return{'result':'fail', 'reason':'server is not ready'}

        #pdu obj create:
        pdu_info = self.options.get('pdu')
        self.logger.info('trying to connect PDU ' + pdu_info.get('ip') + '...')
        pdu = self.get_obj(pdu_info.get('ip'))
        delay = 6 #delay seconds between power off and on
        pdu_port = pdu_info.get('ac_port')

        wait_bmc_time = 150 #seconds, wait time for bmc or os ready
        for i in range(power_cycle_times):
            self.logger.info('testing for the ' + str(i+1) + ' cycle...')
            #the last step:
            if i == power_cycle_times-1: # the last time to power cycle
                #testing shutdown os before the policy test:
                #time.sleep(wait_time) #wait for bmc ready after pdu AC power on
                self.logger.info('power on the DUT server with band-out way.')
                bmc_obj.cmd('chassis power on')
                #ping os before try to shutdown it use os cmd:
                wait_os_ready_time = 300
                if not self.ping(server_info.get('ip'), max_time=wait_os_ready_time):
                    self.logger.error('DUT ip can\'t ping when trying to shutdown it.')
                    return {'result':'fail', 'reason':'OS can\'t ping after '+str(wait_os_ready_time)+' of AC power on in cycle ' + str(i+1)}
                
                self.logger.info('try to shutdown OS before AC power off.')  
                server_obj.shutdown()

            self.logger.info('start power off and power on the DUT with off time ' + str(delay) + 's')
            pdu.power_cycle(pdu_port, delay=delay)
            self.logger.info('wait for ' + str(delay) + 's for AC power on.')
            time.sleep(delay) #wait for AC power on
            
            self.logger.info('will check BMC online status after ' + wait_bmc_time + 's...')
            time.sleep(wait_bmc_time)
            bmc_ping_pass = self.ping(bmc_ip)
                
            if bmc_ping_pass:
                output = bmc_obj.cmd('chassis power status', return_list=False)

                if re.search('Chassis Power is on', output, re.I):
                    self.logger.error('DUT server powered on under alway-off policy. Test failed.')
                    return {'result':'fail', 'reason':'system booted under always-off policy in ' + str(i+1) + ' cycle'}
                elif re.search('Chassis Power is off', output, re.I):
                    self.logger.info('DUT server keeps off after AC power on.')
                else:
                    self.logger.error('BMC not ready for ipmi cmd after ' + wait_bmc_time + 's. Test failed.')
                    return {'result':'fail', 'reason':'BMC not ready for ipmi cmd after ' + wait_bmc_time + 's in' + str(i+1) + ' cycle'}
            else:
                self.logger.error('BMC can\'t ping after AC power on ' + str(wait_bmc_time) + 's')
                return {'result':'fail', 'reason':'bmc ping failed after AC power on ' + str(wait_bmc_time) + 's'}

            #end for loop
        
        return {'result':'pass'}

    

    def test_chassis_always_on(self):
        '''
        description: test for bmc chassis always_on policy, pdu is required for this case
                     tp-5400 : SERV-STFT-BMC-0004_Restore on AC Power Loss-Last state
        author: yuhanhou
        params: NA
        return: result, dict of 
                {
                    'result': 'pass|fail'
                    'reason': 'some_fail_reason'
                }
        '''
        #get bmc info:
        server_info = self.options.get('server') 
        server_obj = self.get_obj(server_info.get('ip'))

        self.logger.info('set always-on on DUT...')
        server_obj.cmd('ipmitool chassis policy always-on')

        #pdu obj create:
        pdu_info = self.options.get('pdu')
        pdu = self.get_obj(pdu_info.get('ip'))

        #bmc obj create:
        bmc_ip = server_info.get('bmc_ip')        
        bmc_obj = self.get_obj(bmc_ip)

        delay = 6 #delay seconds between power off and on
        pdu_port = pdu_info.get('ac_port')

        power_cycle_times = int(self.options.get('testcase').get('cycle', 4)) #the last time need shutdown OS first before AC power cycle
        #check server's power status before test:
        output = bmc_obj.cmd('chassis power status', return_list=False)
        if not re.search('Chassis Power is on', output, re.I):
            self.logger.error('Server is off which is not ready for this test!')
            return{'result':'fail', 'reason':'server is not ready'}

        wait_bmc_time = 150 #seconds, wait time for bmc or os ready
        for i in range(power_cycle_times):
            self.logger.info('testing for the ' + str(i+1) + ' cycle...')
            #the last step:
            if i == power_cycle_times - 1: # the last time to power cycle
                #testing shutdown os before the policy test:
                wait_os_ready_time = 300

                #ping os before try to shutdown it use os cmd:
                if not self.ping(server_info.get('ip'), max_time=wait_os_ready_time):
                    self.logger.error('DUT ip can\'t ping when trying to shutdown it.')
                    return {'result':'fail', 'reason':'OS can\'t ping after '+str(wait_os_ready_time)+' of AC power on in cycle ' + str(i+1)}
                
                self.logger.info('try to shutdown OS before AC power off.')  
                server_obj.shutdown()
                

            self.logger.info('start power off and power on the DUT with off time ' + str(delay) + 's')
            pdu.power_cycle(pdu_port, delay=delay)
            self.logger.info('wait for ' + str(delay) + 's for AC power on.')
            time.sleep(delay) #wait for AC power on
            
            self.logger.info('will check BMC online status after ' + wait_bmc_time + 's...')
            time.sleep(wait_bmc_time)
            bmc_ping_pass = self.ping(bmc_ip)
                
            if bmc_ping_pass:
                output = bmc_obj.cmd('chassis power status', return_list=False)
                if re.search('Chassis Power is off', output, re.I):
                    self.logger.error('DUT can\'t be started under policy always-on.')
                    return {'result':'fail', 'reason':'system is not booted under always-on policy in ' + str(i+1) + ' cycle'}
                elif re.search('Chassis Power is on', output, re.I):
                    self.logger.info('DUT server powered on after AC power on.') 
                else:
                    self.logger.error('BMC not ready for ipmi cmd after ' + wait_bmc_time + 's. Test failed.')
                    return {'result':'fail', 'reason':'BMC not ready for ipmi cmd after ' + wait_bmc_time + 's in' + str(i+1) + ' cycle'}

            else:
                self.logger.error('BMC can\'t ping after AC power on ' + str(wait_bmc_time) + 's')
                return {'result':'fail', 'reason':'bmc can\'t ping after ' + str(wait_bmc_time) +'s in ' + str(i+1) + ' cycle'}
                
            #end for loop
        #wait for os network ready
        
        return {'result':'pass'}



    def test_chassis_previous_policy(self):
        '''
        description: test for bmc chassis always-on policy, pdu is required for this case
                     tp-5402 : SERV-STFT-BMC-0006_Restore on AC Power Loss-Power on	
        author: yuhanhou
        params: NA
        return: result, dict of 
                {
                    'result': 'pass|fail'
                    'reason': 'some_fail_reason'
                }
        '''
        #get bmc info:
        server_info = self.options.get('server') 
        server_obj = self.get_obj(server_info.get('ip'))
        self.logger.info('set chassis policy previous on DUT...')
        server_obj.cmd('ipmitool chassis policy previous')

        #pdu obj create:
        pdu_info = self.options.get('pdu')
        pdu = self.get_obj(pdu_info.get('ip'))

        #bmc obj create:
        bmc_ip = server_info.get('bmc_ip')        
        bmc_obj = self.get_obj(bmc_ip)

        delay = 6 #delay seconds between power off and on
        pdu_port = pdu_info.get('ac_port')

        power_cycle_times = int(self.options.get('testcase').get('cycle', 4)) #the last time need shutdown OS first before AC power cycle
        #check server's power status before test:
        output = bmc_obj.cmd('chassis power status', return_list=False)
        if not re.search('Chassis Power is on', output, re.I):
            self.logger.error('Server is off which is not ready for this test!')
            return{'result':'fail', 'reason':'server is not ready'}

        previous_state = 'on' #previous system status is on
        wait_bmc_time = 150 #seconds, wait time for bmc or os ready
        for i in range(power_cycle_times):
            self.logger.info('testing for the ' + str(i+1) + ' cycle...')
            #the last step:
            if i == power_cycle_times - 1: # the last time to power cycle
                #testing power off before the policy test:
                self.logger.info('power off the DUT with band-out way.')
                bmc_obj.cmd('chassis power off', return_list=False) #power off the system before AC power cycle
                self.logger.info('wait for 30s for DUT off')
                time.sleep(30) #wait for for system off
                output = bmc_obj.cmd('chassis power status', return_list=False)
                if re.search('Chassis Power is off', output, re.I):
                    previous_state = 'off'
                else:
                    self.logger.error('can\'t power off DUT with band-out way. test failed.')
                    return {'result':'fail', 'reason':'system is not off after band-out power off in' + (wait_time) + 's'}
            
            self.logger.info('start power off and power on the DUT with off time ' + str(delay) + 's')
            pdu.power_cycle(pdu_port, delay=delay)
            self.logger.info('wait for ' + str(delay) + 's for AC power on.')
            time.sleep(delay) #wait for AC power on
            
            self.logger.info('will check BMC online status after ' + wait_bmc_time + 's...')
            time.sleep(wait_bmc_time)
            bmc_ping_pass = self.ping(bmc_ip)
            if bmc_ping_pass:
                output = bmc_obj.cmd('chassis power status', return_list=False)
                if not re.search('Chassis Power is ' + previous_state, output, re.I):
                    self.logger.error('DUT can\'t stay  previous status ' + previous_state + ' after AC power on')
                    return {'result':'fail', 'reason':'system is not booted under always-on policy in ' + str(i+1) + ' cycle'}
            
            else:
                self.logger.error('BMC can\'t ping after AC power on ' + (wait_bmc_time) + 's')
                return {'result':'fail', 'reason':'bmc can\'t ping after ' + (wait_bmc_time) +'s in ' + str(i+1) + ' cycle'}
                
            #end for loop
        return {'result':'pass'}
