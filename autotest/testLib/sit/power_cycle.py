from autotest.testLib.base import Base

class PowerCycle(Base):
    '''
    description: this class is test library for power cycle
    author: yuhanhou
    '''

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)
    
    
    def test_powercycle(self):
        '''
        description: this is a demo test for power cycle which running on DUT locally
        author: yuhanhou ; updater: rexguo
        params: NA
        return: result, dict of 
                {
                    'result': 'pass|fail'
                    'reason': 'some_fail_reason'
                }
        '''
        server_info = self.options.get('server')
        server_obj = self.get_obj(server_info.get('ip'))
        script_opt = self.options.get('testcase', {}).get('script_opt', '')
        #.sh script is only running on linux, so just put the linux path seperator in str in following statement
        server_obj.cmd('cd ' + server_obj.tea_path + server_obj.path_sep + 'standalone/common_test/power-cycle')
        server_obj.run_script('standalone/common_test/power-cycle/power_cycle.sh', opts=script_opt, bkground=True)
        
        self.collect_original_script_logs('power-cycle')
        
        if '--reboot' in script_opt and '--dccycle' in script_opt:
            logfile = 'standalone/common_test/power-cycle/reports/osreboot_dccycle.log'
        elif '--reboot' in script_opt:
            logfile = 'standalone/common_test/power-cycle/reports/reboot.log'
        elif '--dccycle' in script_opt:
            logfile = 'standalone/common_test/power-cycle/reports/dccycle.log'
        elif '--accycle' in script_opt:
            logfile = 'standalone/common_test/power-cycle/reports/accycle.log'
        return self.check_original_script_status(logfile)





