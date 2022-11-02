from argparse import MetavarTypeHelpFormatter
from genericpath import exists
import re
import time
import os, platform
import pprint
import shutil
from datetime import datetime
from common.communication.local import Local
from common.other.log import Logger
from common.infrastructure.factory import HardwareFactory
from common.infrastructure.server.factory import ServerFactory
from common.infrastructure.sm.bmc import BMC
from common.infrastructure.dm.pdu import PDU

#from common.infrastructure.server.factory import Factory

class Base():
    '''
    decription: this class is base testlib for all tests
    author: yuhanhou
    '''

    def __init__(self, **kwargs):
        '''
        description: init method for test lib
        author: yuhanhou
        params: kwargs, optional kw pairs
                    {
                        'server':{ip:xxip, user:xxuser password:xxx bmc_ip:xxbmc bmc_user:yyuser bmc_password:bpwd},
                        'testcase':{name:t1, loop:2, tool:xxtool, lib:sit.processor.XXclass, testplan=test001, project=palos, full_name=tp1:testcase1},
                         run_mode: remote(default) or local # to record the running is on dut or remote test engine 
                    }
        return: NA 
        '''
        self.options = kwargs
        self.local_runs = [] #bandin testcase list which is running on dut
        self.obj_pool = {} # ip:obj

        #create logs dir 
        server_info = self.options.get('server', {})
        ip = server_info.get('ip', server_info.get('bmc_ip'))
        self.testcase = self.options.get('testcase').get('case_func') #this testcase is a real testcase func name
        self.log_path = self.create_logs_dir(server=ip, testcase=self.testcase)
        self.log_file = os.path.join(self.log_path, self.testcase + '.log')
        
        self.logger = Logger(log_file=self.log_file, log_file_timestamp=False) #no timestamp add for tea.log file name

        #samba server for log collection:
        self.smb_share = self.options.get('smb_share', '10.49.29.37:auto') #can set default here
        self.smb_user = self.options.get('smb_user', 'tea')
        self.smb_pwd = self.options.get('smb_pwd', 'autopassword')
        self.smb_sub_dir = self.options.get('smb_sub_dir', '')
        self.smb_client_mnt = self.options.get('smb_client_mnt', '/samba')
         

    def local_register(self, testcase):
        '''
        description: this is a register to record the testcase drifting to run on dut local
        author: yuhanhou
        params: testcase, which is registered to a local DUT case
        return: NA
        '''
        self.local_runs.append(testcase)


    def fct_test(self, **kwargs):
        '''
        description: this is an interface to start factory testing scenario
        author: yuhanhou
        params: kwargs, optional kw pairs
        return: NA
        '''        
        pass


    def test(self, **kwargs):
        '''
        description: interface for test case running
        author: yuhanhou
        params: kwargs, keywards or unpacking dict to update self.options
        return: testcase func's return value
        '''
      
        self.options.update(kwargs)
        
        self.logger.info('Start to run testcase:' + self.testcase)
            
        self.logger.info('===============test case parameters=============')
        # tmp_opts = self.options.copy()
        # template = '{0:20s}{1:45s}'
        # self.logger.info(template.format('testcase:', tmp_opts.pop('testcase', 'N/A')))
        # self.logger.info(template.format('profile:', tmp_opts.pop('profile', 'N/A')))
        # self.logger.info(template.format('total loops:', str(tmp_opts.pop('loop', 'N/A'))))
        # self.logger.info(template.format('current loop:', str(tmp_opts.pop('loop_id', 'N/A'))))
        # self.logger.info(template.format('run_type:', tmp_opts.pop('type', 'N/A')))
        # self.logger.info(template.format('case_log:', self.logger.log_file))
        # self.logger.info('='*80 + '\n')
        
        # if os.environ.get('DEBUG') == '1':
        #     self.logger.info('other parameters:')
        #     self.logger.info(pprint.pformat(tmp_opts, indent=4))

        self.logger.info(pprint.pformat(self.options, indent=4))

        #debug:
        # lib = str(self.options.get('testcase').get('lib'))
        # print('==daisy, liib:' + lib)


        if self.testcase in self.local_runs and self.options.get('run_mode', '') != 'local':
            #get current module path and class name, testcase name to all the exactly method
            # cls_name = self.__class__.__name__
            # mod_name = __name__

            #the py path should be changed to each os type
            # opt_str = '-m ' + mod_name + ' -c ' + cls_name
            opt_str = ''

            for k, v in self.options.items():
                if v == None:
                    continue
                if k == 'testcase':
                    opt_str += ' -i '
                    for tk, tv in v.items():
                        if tv == None:
                            continue
                        if tk == 'lib':
                            match = re.search('class\s+\'(\S+)\'', str(tv))
                            if match:
                                tv = match.group(1)
                       
                        opt_str += tk + '="' + tv + '",'
                elif re.search('server', k, re.I):
                    if v == None:
                        continue                    
                    opt_str += ' -s ' 
                    for sk, sv in v.items():
                        if sv == None:
                            continue                         
                        opt_str += sk + '=' + sv + ','
                elif re.search('pdu', k, re.I):
                    pass
                else:
                    if v == None:
                        continue
                    elif isinstance(v, bool):
                        opt_str += ' -o ' + k
                    else:              
                        opt_str += ' -o ' + k + '="' + v + '"'

         
            server_info = self.options.get('server')
            server_obj = self.get_obj(server_info.get('ip'))
            #call the local case runner to start case locally on server under test:
            #the run_scripts will read the tea/standalone
            self.logger.info('run scripts on ' + server_obj.ip)
            script = 'standalone' + server_obj.path_sep + 'local_case_runner.py'
            self.logger.info(script + ' ' + opt_str)
            server_obj.run_script(script, opts=opt_str, bkground=True, program='python3')

            result = {}

            # check the result of testcase running on local server:
            self.logger.info('try to parse local runner case result...')
            while True:
                result = self.get_local_case_result()

                if result:
                    break
                else:
                    time.sleep(2)
                
            return result
        
        else:
            
            func = getattr(self, self.testcase)

            loop = int(self.options.get('testcase').get('loop', 1))
            server_info = self.options.get('server', {})
            ip = server_info.get('ip', server_info.get('bmc_ip')) 
            smb_sub_dir = self.smb_sub_dir.replace('/', os.pathsep)           
            smb_log_path = self.smb_share + '/' + smb_sub_dir + '/' + ip  + '/' + self.testcase
            result = {'log':smb_log_path}

            for i in range(1, loop+1):
                result.update(func())
                if result.get('result') == 'fail':
                    break
            
            self.logger.info('test result: ' + result.get('result', ''))
            self.logger.info('test comment: ' + result.get('reason', ''))
            self.logger.info('uploaded logs: ' + result.get('log', ''))

            #collect logs
            self.collect_logs()



            self.logger.info(result)
            return result
      

    def test_demo(self):
        time.sleep(1)
        raise Exception('errorrr')
        print('this is a test')




    def test_demo2(self):
        time.sleep(1)
        print('this is a test')








    def ping(self, ip, **kwargs):
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
        max_time = kwargs.get('max_time')
        delay_time = int(kwargs.get('delay_time', 10))
        retry_time = int(kwargs.get('retry_time', 3))#retry_time will be overwrite by max_time/delay_time if max_time defined
        
        if max_time:
            retry_time = int(max_time)//delay_time

      
        result = False
        ping_count = 1
        local_cmd = Local()
        self.logger.info('checking network connection of ip ' + ip)
        while True:
            cmd_out = local_cmd.cmd('ping -c 3 ' + ip, return_list=False)
            ping_count += 1
            
            if re.search('100% packet loss', cmd_out, re.I):
                self.logger.info("host " + ip + " is not available!")
                result = False
            elif re.search(r'.*\s0% packet loss', cmd_out, re.I):
                self.logger.info("network of " + ip + " is ok.")
                result = True
            elif re.search(r'(.*\s[3-6][3-6]% packet loss)', cmd_out, re.I):
                    self.logger.warn(ip + " has networking issue. Please check it!")
                    m = re.search(r'(.*\s[3-6][3-6]% packet loss)', cmd_out, re.I)
                    result =  m.group(0)
            
            if result != True and ping_count <= retry_time:
                self.logger.info('waiting for ' + str(delay_time) + 's to retry ping again...')
                time.sleep(delay_time)
            else:
                return result


    def get_obj(self, ip, **kwargs):
        '''
        description: this method is used to get hw object
        author: yuhanhou
        params: ip, ip of the hw, include os, bmc or other hw ip
        return: ip related hw type object
        '''
        if ip in self.obj_pool and self.obj_pool.get(ip) != None:
            return self.obj_pool.get(ip)
        else:
            hw_info = self.get_hw_info(ip)
            hw_info.update(kwargs)
            obj = HardwareFactory.create_hw_obj(log_path=self.log_path,**hw_info)
            
            self.obj_pool[ip] = obj
            return obj




    def get_hw_info(self, ip):
        '''
        description: this method is used to get hw info from the ip
        author: yuhanhou
        params: ip, ip of the hw, include os, bmc or other hw ip
        return: hw_info     
        '''
        
        hw_type = ''
        hw_info = {}

        for item_type, dict_info in self.options.items():

            if 'ip' in dict_info and ip == dict_info.get('ip'):
                hw_type = item_type
                hw_info = dict_info
                break

            elif 'bmc_ip' in dict_info and ip == dict_info.get('bmc_ip'):
                hw_type = 'bmc'

                for k, v in dict_info.items():
                    match = re.search(r'bmc_(\S+)', k, re.I)
                    if match:
                        hw_info[match.group(1)] = v
                break #skip the upper for loop

        hw_info.update(hw_type=hw_type)

        return hw_info


    def create_logs_dir(self, **kwargs):
        '''
        description: create logs dir for each server and each testcase
        author: yuhanhou
        params: kwargs, optional kw pairs
                    server, server ip 
                    testcase, testcase func name
        return: NA
        '''

        #gen the  default log path: test/logs/serverxx/testcasexx
        print('creating log dirs under tea/test/logs...')
        cur_path = os.path.abspath(__file__)
        test_dir_path = os.path.dirname(cur_path) 

        match = re.search(r'(\S+)\StestLib', cur_path, re.I)

        if match:
            test_dir_path = match.group(1)

        server = kwargs.get('server', '')
        testcase = kwargs.get('testcase', '')
        log_path = os.path.join(test_dir_path, 'logs', server, testcase) #test/logs/ip/casename

        #create logs dir:
        #if os.path.exists(log_path) and self.options.get('run_mode', '') == 'local':
        if os.path.exists(log_path):
            bk_log_path = ''
            match = re.search(r'(\S+)tea', log_path)
            if match:
                bk_log_path = os.path.join(match.group(1), 'bk_logs' , testcase + '_' + datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            
            shutil.copytree(log_path, bk_log_path)
            shutil.rmtree(log_path)

        os.makedirs(log_path, exist_ok=True)

        return log_path


    def collect_logs(self, **kwargs):
        '''
        description: collect server's OS system logs and upload all the logs to samba server:
                     samb_share/timestamp/ip/testcase/xx.logs
                     could add collect bmc logs in future
        author: yuhanhou
        params: kwargs, optional kw pairs, TBD
                
        return: NA 
        '''
        server_info = self.options.get('server')
        self.logger.info('collect logs to samba server...')

        if server_info.get('ip') != 'localhost' and self.ping(server_info.get('ip'), retry_time=3): #this test with a OS ip provided will collect the system logs
            #collect system logs
            server_obj = self.get_obj(server_info.get('ip'))
            server_obj.collect_sys_logs()  #如果是远程case，dut上的log dir并不存在，如何收集-已解决？

            #upload logs from server to samba:
            server_obj.mount_smb(self.smb_share, user=self.smb_user, password=self.smb_pwd)
            #mountxx/timestamp/ip/testcase/xx.logs
            sep = server_obj.path_sep
            smb_sub_dir = self.smb_sub_dir.replace('/', sep) #for try_run mode sub_dir is: try_run/timestamp
            target_path = sep.join([server_obj.mount_point, smb_sub_dir, server_obj.ip]) 
            server_obj.raw_copy(server_obj.local_log_path, target_path)

        #upload remote testcase logs on test engine to samba:
        if self.options.get('run_mode', '') != 'local':
            tea_os = self.get_currect_os_obj(mount_point=self.smb_client_mnt)
            target_path = tea_os.path_sep.join([tea_os.mount_point, self.smb_sub_dir, server_info.get('ip', server_info.get('bmc_ip'))])
            tea_os.raw_copy(self.log_path, target_path)
        
        self.logger.info('collect logs to samba server done.')
   

    def get_local_case_result(self):
        '''
        description: get testcase result on running on server locally by parse logs uploaded on samba
                     this method is running on tea OS
        author: yuhanhou
        params: NA
        return: NA 
        '''

        result = {}

        tea_os = self.get_currect_os_obj(mount_point=self.smb_client_mnt) #current tea os
        server_info = self.options.get('server')
        server_ip = server_info.get('ip')
        smb_sub_dir = self.smb_sub_dir.replace('/', os.pathsep)
        test_log = os.path.join(tea_os.mount_point, smb_sub_dir, server_ip, self.testcase, self.testcase + '.log')
        
        if not os.path.exists(test_log):
            return result

        #get the test log content
        content = ''
        with open(test_log, 'r') as f:
            content = f.read()

        match = re.search(r'test result:\s*(\S+)', content, re.I)
        
        if match:
            result['result'] = match.group(1)
             
        comment_match = re.search(r'test comment:\s*(.+)\s*\n', content, re.I)
        if comment_match:
            result['reason'] = comment_match.group(1)
        
        

        log_match = re.search(r'uploaded logs:\s*(.+)\s*\n', content)
        if log_match:
            result['log'] = log_match.group(1)

        

        return result


    def check_original_script_status(self, log):
        '''
        description: get original scripts status running on dut locally and copy the original logs into tea log folder
        author: yuhanhou
        params: log, log path on dut relative to the root scripts path(/scripts)
        return: result, dict of 
                {   'result':'pass|fail'
                    'reason':'some_fail_reason
                } 
        '''

        result = {}

        server_info = self.options.get('server')
        server_obj = self.get_obj(server_info.get('ip'))
        log_path = server_obj.tea_path + server_obj.path_sep + re.sub('/', server_obj.path_sep, log) 


        while True:
            script = 'standalone' + server_obj.path_sep + 'original_log_parser.py'
            out = server_obj.run_script(script, opts='-p ' + log_path, program='python3')
           
            if not re.search(r'test done', out, re.I):
                time.sleep(3)
                continue
            else:
                match = re.search('result:(.*?)\s*reason:(.*?)\s*\n', out, re.I)
                if match:
                    result['result'] = match.group(1)
                    result['reason'] = match.group(2)

                    #copy the scripts log into tea/test/logs folder
                    #log_dir_path = os.path.dirname(log_path)
                    #server_obj.raw_copy(log_dir_path, server_obj.local_log_path)

                
                return result
        

    def collect_original_script_logs(self, script_dir, log_dir='reports'):
        '''
        description: copy the original logs into 'tea/test/logs/script_dir/' on dut.
        author: yuhanhou
        params: script_dir, original script dir names, like SIT-Power-CycleTest, 
        return: NA
        '''
        server_info = self.options.get('server')
        server_obj = self.get_obj(server_info.get('ip'))
        src_log_path = server_obj.tea_path + server_obj.path_sep \
                        + 'standalone' + server_obj.path_sep + script_dir + server_obj.path_sep + log_dir
        
        des_log_path = server_obj.local_log_path + server_obj.path_sep + script_dir

        server_obj.raw_copy(src_log_path, des_log_path)


    def get_currect_os_obj(self, **kwargs):
        '''
        description: get current os which is running this module
        author: yuhanhou
        params: kwargs, optional keywords params
        return: currect OS object
        ''' 
        if not hasattr(self, 'current_os') or self.current_os == None:
            
            self.current_os = ServerFactory.create_server_obj(protocol='local', **kwargs)
           
        return self.current_os
    












                







        




