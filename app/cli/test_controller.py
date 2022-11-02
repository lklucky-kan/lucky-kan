#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import re, copy
import json
import pprint
import os, sys
from datetime import datetime
tea_path = __file__.split('tea')[0]+'tea'
sys.path.append(tea_path)
import time
tea_path = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.pardir,
        os.pardir
    )
)
sys.path.append(tea_path)
from common.other.log import Logger
from common.other.concurrence import multi_threads, multi_processes
from common.infrastructure.server.factory import ServerFactory
from common.communication.local import Local
from common.communication.transfer import FileTransfer
from autotest.testLib.factory import TestFactory
from threading import Thread
from common.other.test_linker import TestLinkManager
from common.file.csv_parser import CSV_Parser
from common.file.yaml_profile import YamlProfile
from common.file.json_rw import fopen, Pack

class TestController():
    '''
    description: this class is used for control test flow.
    author: yuhanhou
    '''

    def __init__(self, options, **kwargs):
        '''
        description: this method is to start test flow
        author: yuhanhou
        params: options, dict of the test related params:
                    {
                        server:[{'ip=xxip, user=xxuser, password=xxx, bmc_ip=xxbmc, bmc_user=yyuser, bmc_password=bpwd'},
                                {'ip=xxip, user=xxuser, password=xxx, bmc_ip=xxbmc, bmc_user=yyuser, bmc_password=bpwd'},
                                ...
                                ]
                   

                        testcase:[{'name=t1, loop=2, tool=xxtool, testsuite=processor'},
                                  {'name=t2, loop=2, tool=xxtool, testsuite=processor'},
                                    ...
                                 ]
                        
                        objs:{ ip1:obj1,
                               ip2:obj2,
                                 ...
                             }

                        smb_share: 
                        
                    }

        '''
        self.logger = kwargs.get('logger', Logger(log_file='tea.log'))
        self.logger.info('test manager is initialized...')
        self.servers = options.pop('server', [])
        self.testcases = options.pop('testcase', [])
        self.options = options
        self.smb_share = self.options.get('smb_share', '10.67.13.242:auto') #can set default here
        self.smb_user = self.options.get('smb_user', 'tea')
        self.smb_pwd = self.options.get('smb_pwd', 'autopassword')
        timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
        self.run_time = timestamp  #to create a timestamp dir on samba share folder to put all the logs
        if 'runner' in self.options: #for dev testing or acceptance testing mode
            self.run_time = self.options.get('runner') + '/' + self.run_time

        smb_client_mnt = self.options.get('smb_client_mnt', '/samba')
        self.tea_os = ServerFactory.create_server_obj(protocol='local', log_file_timestamp=timestamp, mount_point=smb_client_mnt)

    def start(self, method='async', **kwargs):
        '''
        description: this method is to start test flow
        author: yuhanhou
        params: method, async or sync, default is async, means all the DUTs run their own testcase separately or in sync 


                kwargs, optional keyword options 

                        
        return: NA
        '''

        try:
            self.tear_up()
        except Exception as e:
            raise(e)


        proc_opts = []

        if self.testcases != None and len(self.testcases) == 0:
            raise Exception('no testcases are selected!')
        
        if self.servers !=None:
            for server_info in self.servers:
                proc_opts.append({'args':[server_info, self.testcases]})

        #debug
        print(pprint.pformat(proc_opts, indent=4))

        # global stop
        # stop = False
        # monitor = Thread(self.monitor()) #start monitor thread or proc
        # monitor.start()
        multi_result = {}

        if len(proc_opts) > 0 :
            multi_result = multi_processes(self.async_test_flow, opts=proc_opts)
        # print(pprint.pformat(multi_result, indent=4))

        tmp_dict = {}

        #  1: {   'result': {   '192.168.56.136': {   'demo_cpu1': {   'log': '10.49.28.129:auto/2021_05_19_14_00_32/test_demo_cpu1',
        #                                                         'result': 'pass'},
        #                                        'demo_cpu2': {   'log': '10.49.28.129:auto/2021_05_19_14_00_32/test_demo_cpu2',
        #                                                         'reason': 'cpu2',
        #                                                         'result': 'fail'}}}
        for v in multi_result.values():
            tmp_dict.update(v.get('result'))
        
        self.report(tmp_dict)






        # stop = True
        # monitor.join()

        # self.tear_down()

    def report(self, results):
        '''
        description: print summary report for all tests for one server
        author: yuhanhou
        params: result of testcase with structure
                {'192.168.56.136': {'demo_cpu1': { 'log': '10.49.28.129:auto/2021_05_19_13_41_13/test_demo_cpu1',
                                                     'result': 'pass'},
                                    'demo_cpu2': {'log': '10.49.28.129:auto/2021_05_19_13_41_13/test_demo_cpu2',
                                                  'reason': 'cpu2',
                                                  'result': 'fail'}
                                },
                 ...
                }
        return: NA
        '''

        titles = ['testcase', 'result', 'comment', 'log']
        template = '{0[0]:30s}{0[1]:15s}{0[2]:30s}{0[3]:50s}'
        print(pprint.pformat(results, indent=4))
        
        summary_file = open('result', 'w')
        summary_file.write('*************************Test Summary Report*************************\n')
        
        print('*************************Test Summary Report*************************')




        for ip, result in results.items():
            total_case = len(result.keys())
            total_pass = len([c for c in result if result.get(c).get('result') == 'pass'])
            total_fail = len([c for c in result if result.get(c).get('result') == 'fail'])
            line = '\nserver:' + ip + '    total:' + str(total_case) + '    pass:'+ str(total_pass) + '    fail:' + str(total_fail)

            print(line)
            summary_file.write(line + '\n')

            print('---------------------------------------------------------------')
            summary_file.write('---------------------------------------------------------------\n')

            print(template.format(titles))
            summary_file.write(template.format(titles) + '\n')

            for testcase, case_result in result.items():
                columns = [testcase, case_result.get('result'), case_result.get('reason', ''), case_result.get('log', '')]
                
                print(template.format(columns))
                summary_file.write(template.format(columns) + '\n')


    
    def monitor(self, **kwargs):
        '''
        description: monitor all the servers testing status by watching the log file
        author:
        params:
        return:
        '''
        global stop

        while not stop:
            print("I'm a dump monitor!")
            time.sleep(5)


    def async_test_flow(self, server_info, case_info_list):
        '''
        description: start testcases in flow for signle DUT
        author: yuhanhou
        params: server_info, dict of DUT info, 
                    {ip:xxip, user:xxuser password:xxx bmc_ip:xxbmc bmc_user:yyuser bmc_password:bpwd}
                case_info_list,
                    [{testcase:t1, loop:2, tool:xxtool, mod_info:sit.processor.XXclass},
                     {testcase:t2 loop=2, tool=xxtool, mod_info=sit.xx.xx},
                      ...
                    ]
        return: NA 
        '''
        result = {server_info.get('ip', server_info.get('bmc_ip')):{}}
        
        #debug
        print ('in async test flow!')
        print(case_info_list)
        print(server_info)

        for case_info in case_info_list:

            result[server_info.get('ip',server_info.get('bmc_ip'))][case_info.get('name')] = self.single_test(case_info, server_info)
            self.logger.info(server_info.get('ip', server_info.get('bmc_ip')) + ' testcase: ' + case_info.get('name') + ' result is')
            print(json.dumps(result, indent=4))

        return result


        
    def single_test(self, case_info, server_info):
        '''
        description:
        author:
        params:
        return:
        '''
        if self.options.get('framework') == 'tea':
            try:
                result = self.exe_tea(case_info, server_info)
                #upload result to testlink
                #self.upload_result_to_testlink(result)
            except Exception as e:
                result = {'result':'fail', 'reason':str(e)}
                raise(e) #for debug

            return result

        elif self.options.get('framework') == 'robot':
            return self.exe_robot(case_info, server_info)
        elif self.options.get('framework') == 'selenium':
            return self.exe_selenium(case_info, server_info)

        #collect logs from dut to remote dir




    def exe_tea(self, case_info, server_info):
        '''
        description:
        author:
        params: case_info , dict of case info
                    {name:t1, loop:2, tool:xxtool, lib:sit.processor.XXclass}
        return:
        '''

        other_opts = {
            'smb_sub_dir':self.run_time,
            'smb_share':self.smb_share,
            'smb_user':self.smb_user,
            'smb_pwd':self.smb_pwd,
        }

        other_opts.update(self.options)
        case = TestFactory.create_testcase(case_info.get('lib'), testcase=case_info, server=server_info, **other_opts)
        result = case.test()

        #prepare testlink result upload parameter in result dict:
        if 'full_name' in case_info and 'project' in self.options and 'testplan' in self.options:
            project = self.options.get('project')
            testplan = self.options.get('testplan')
            casename = case_info.get('full_name')
            case_id = casename.split(':').pop(0)
            result.update(project=project,testplan=testplan,case_id=case_id)
            if 'platform' in case_info:
                platform = case_info.get('platform')
                result.update(platform=platform) 

        #add logs path into result which will be upload into testlink:
        log_path = self.tea_os.mount_point + self.tea_os.path_sep + self.run_time +  self.tea_os.path_sep  + server_info.get('ip', server_info.get('bmc_ip')) +  self.tea_os.path_sep + case_info.get('name')
        logs = []
        for dirpath, dirnames, filenames in os.walk(log_path):
            for filename in filenames:
                logs.append(os.path.join(dirpath,  filename))

        result.update(logs=logs)

        return result



    def exe_robot(self, case_info, server_info):
        # robot_path = factory.find_robot_file(**kwargs)
        # subprocess.check_output("robot " + robot_path + '--vars') #add loop and other parameter info
        #robot的case的参数要把kwargs组织一下发给robot可处理，或者作为导入库的参数直接实例化？
        pass

    def exe_selenium(self, case_info, server_info):
        pass



    def prepare_server(self): #下发脚本
        '''
        description: this method is used to distribute scritps to servers under test, prepare the python3 run env on dut
        author: yuhanhou
        params: NA 
        return: NA 
        '''

        cur_path = os.path.dirname(os.path.realpath(__file__))
        #match = re.search(r'(\S+tea)', cur_path)


        #if match:
        #upload current tea package to samba server
        #tea_path = match.group(1)
        #remove .git from tea due ti this dir is very big, will impact the transfer speed.
        self.tea_os.cmd(f'rm -rf {tea_path}/.git')
        self.tea_os.cmd('chmod 755 -R ' + tea_path)
        self.options['smb_client_mnt'] =  self.tea_os.mount_smb(self.smb_share, user=self.smb_user, password=self.smb_pwd)  #assure no user/password here

        mnt_share_dir = self.tea_os.mount_point + self.tea_os.path_sep + self.run_time #this folder can store logs of this test

        self.tea_os.cmd('mkdir ' + mnt_share_dir) #create the timestamp scripts dir to avoid mutiple jobs on jenkins

        #all the dut's get tea from samba server, the server must have a OS ip which can be accessed!
        proc_opts = []
        servers = [s for s in self.servers if 'ip' in s]
        #proc_opts.append({'args':[server_info, testcases]})
        for server_info in servers:
            proc_opts.append({'args':[server_info, self.run_time, 'tea']})

        if len(proc_opts) > 0 and not self.options.get('nodist'):
            # copy scripts to samba server
            self.logger.info('Pack tea folder to "/tmp/tea.tar.gz"')
            Pack.pack_targz('/tmp/tea.tar.gz', tea_path)
            self.logger.info('copying /tmp/tea.tar.gz to samba server...')
            self.tea_os.raw_copy('/tmp/tea.tar.gz', mnt_share_dir)
            multi_processes(self.dist_scripts_to_server, opts=proc_opts, logger=self.logger)
        #如何配置python运行环境和module包，如果dut无法连外网？默认环境已经提前配好

    def dist_scripts_to_server(self, server_info, *sub_dir):
        '''
        description: distribute scripts to one server
        author: yuhanhou
        params: server_info, dict of server info
                    ip: 
                    user:
                    password:
                    os:
                    ...
                sub_dir: sub dirs under samba shared service folder
        return: NA
        '''
        server_obj = ServerFactory.create_server_obj(**server_info)
        #mount samba on dut:
        server_obj.mount_smb(self.smb_share, user=self.smb_user, password=self.smb_pwd)
        mnt_scritps_on_server = server_obj.mount_point + server_obj.path_sep + server_obj.path_sep.join(sub_dir)
        mnt_scritps_path = server_obj.mount_point + server_obj.path_sep + sub_dir[0]
        #clean old tea scripts folder on DUT server:
        server_obj.clear_tea_scripts()
        
        #copy tea from samba to dut local:
        self.logger.info('decompress the tea.tar.gz in samba path {0}'.format(mnt_scritps_path))
        server_obj.cmd('cd {0} && tar -zxvf tea.tar.gz'.format(mnt_scritps_path))
        self.logger.info('copying tea from samba to DUT servers...')
        server_obj.raw_copy(mnt_scritps_on_server, server_obj.scripts_root_path)

        #copy original scripts to dut local:
        #server_obj.raw_copy(server_obj.mount_point + server_obj.path_sep + 'original', server_obj.scripts_root_path, chmod='755')

        server_obj.session.close()


    def tear_up(self):
        '''
        description: tear up actions before start testing
        author: yuhanhou
        params: NA
        return: NA
        '''  
        self.prepare_server()

        #prepare testcase libs:
        #lookup_case_lib(cls, case, team='sit', framework='tea'):
        team = self.options.get('team', 'sit')
        framework = self.options.get('framework', 'tea')

        # testcase:[{'name=t1, loop=2, tool=xxtool'},
        #             ...
        #          ]

        #get testcase mapping from testlink to tea testlib:
        csv = CSV_Parser(separator=r'\s*,\s*')
        mapping_file = tea_path + '/autotest/profile/case_mapping'
        case_map = {items[0]:items[1] for items in csv.read(mapping_file, data_s='list')}

        for case_info in self.testcases:
            testlink_casename = case_info.get('full_name')
            if 'name' not in case_info: #call from jenkins could not have name defined only having tetslink fullname
                case_info['name'] = case_map.get(testlink_casename)

            case_name = case_info.get('name')
            if case_name == None:
                raise Exception('no testcase name is provided! Please check the cli params and the test/profile/case_mapping file.')

            lib, func = TestFactory.lookup_case_lib(case_name, team, framework)
            case_info.update(lib=lib, case_func=func, name=case_name)
     
 
    def upload_result_to_testlink(self, result):
        '''
        description: upload result into testlink
        author: yuhanhou
        params: result, dict of the testcase result details , include:
                   
                        { 
                            'result':'pass|fail|block'
                            'testplan': testplan name on testlink
                            'project': project name on testlink
                            'case_id': testcase external id
                            'timestamp': testing timestamp
                            'build': optional, default will upload to the latest build
                            'platform': if defined platform for this execution on testlink, \
                                        this is needed.
                            'execduration': minutes(float), optional, duration time of this testcase
                            'logs': list of log files path
                        } 
        
        return: NA
        '''
        if result.get('case_id') != None:
            testlinker = TestLinkManager()
            testlinker.update_testcase_result(result)
        else:
            self.logger.warn('test result will not upload to testlink due to no testlink case info is provided.')




 

    # def start_socket_listener(self, **kwargs):
    #     socket.server.start()

    #     while True:
    #         msg = socket.server.rerv(1024)
    #         if msg == 'please help to start case...':
    #             testcase = testcasexx
    #             result = local.session('robot xx.robot -var xx...')
                
    #             write reuslt to local file_status

    #             send result to dut
    #         elif msg == 'testcase xx done , result is: xx':
    #             write result to local file_status

    #         elif msg == 'all case done' and client is closed:
    #             server.closed
    #             break


def parse_kwPairs2dict(kw_list):
    '''
    description: this method is used to parse the append key=word params in argparse module
    author: yuhanhou
    params: kw_list, list of str with key word pairs
            ['k1=v1', 'k2=v2', 'k3=v3', ...]
                
    return: dict data structure
            {
                'k1':'v1',
                'k2':'v2',
                ...
            }
        '''

    kwargs = {}
    kwargs = {kw[0]:kw[1] for kw in [arg.split('=') for arg in kw_list if re.match(r'\S+=', arg)]}
    for arg in kw_list:
        if not re.search('=', arg) and arg != '':
            kwargs.update({arg:True})

    #remove the '' or "" embracing the value after =, like zz='xx yy zz'
    for k, v in kwargs.items():
        if isinstance(v, str):
            match = re.search(r'^[\'"](.*?)[\'"]$', v)
            if match:
                kwargs[k] = match.group(1)
            

    return kwargs



 
 
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Process the cmdline parameters')
    parser.add_argument('-c','--profile', help='the path of config profile')
    parser.add_argument('-f','--framework', default='tea', help='framework of the test, robot or selenium or tea, default is tea')
    parser.add_argument('-t','--team', default='sit', help='team of the test case. sit, bmc supported')
    parser.add_argument('-i', '--include',  action='append', help='-i testsuite=processor,name=t1(if no name set, full_name is a must),full_name=testlinkfullname,loop=2,tool=xxtool -i ... -i ... ')
    parser.add_argument('-s','--server', action='append',  help='-s ip=xxip,user=xxuser,password=xxx,bmc_ip=xxbmc,bmc_user=yyuser,bmc_password=bpwd -s ... -s ...')
    parser.add_argument('-p','--pdu', help='-p ip=xxip,user=xxuser,password=xxx,ac_port=10')
    parser.add_argument('-o','--optional', action='append', help='optional keywords args like: -o k1=v1 -o k2=v2 -o flag')
    args = parser.parse_args()

    testcases = []
    #parse included test dict info  into testcases list:
    if args.include:
        for test in args.include:
            tmp_list = re.split(r',', test.strip())
            testcases.append(parse_kwPairs2dict(tmp_list))
        # testcases = args.include

    servers = []
    #parse server in test dict info into servers list:
    if args.server:
        for server in args.server:
            tmp_list = re.split(r',', server.strip())
            servers.append(parse_kwPairs2dict(tmp_list))
        # server = args.server
    
    kwargs = {}

    if args.pdu:
        tmp_list = re.split(r',', args.pdu)
        kwargs.update(pdu=parse_kwPairs2dict(tmp_list))

    if args.optional:
        kwargs.update(parse_kwPairs2dict(args.optional))
    
    #currently only support single server in profile for currect requirement.
    #if need support mutiple servers, need modify the profile format
    if args.profile:
        test_data = YamlProfile.parse_single_profile(args.profile)
        #test_project, test_plan考虑放到-o里面，test controller可以修改一下project信息来源
        kwargs.update(project=test_data.get('TestProject'))
        kwargs.update(testplan=test_data.get('TestPlan'))
        #add Server info in profile:
        servers.append(test_data.get('Server'))

        #add pdu info in profile, profile's pdu info will overwrite pdu in cli of this script
        kwargs.update(pdu=test_data.get('PDU'))

        cases_in_profile = [] # to edit the testcases in test profile
        for case in test_data.get('TestCases'):
            case_info = {}
            case_info['full_name'] = case.get('name')
            #args: -c xx --reboot tool=memtest xx=yy
            case_args_str = case.get('args', '')

            if re.search(r'\S+', case_args_str):
                #script_opt is used by the original scripts , if multiple original scripts need multiple, please set k='-xx -yy' and use 'k' value as k script's opt
                script_opt = re.sub(r"\S+=['\"].*?['\"]|\S+=\S+", '', case_args_str)
                if re.search(r'\S+', script_opt):
                    case_info['script_opt'] = script_opt

                case_kwargs_list = re.findall(r"\S+=['\"].*?['\"]|\S+=\S+", case_args_str)
                #['tool=memtest', "tool_args='-l 100 -t now'"]
                case_info.update(parse_kwPairs2dict(case_kwargs_list))
            
            testcases.append(case_info)

                
    kwargs.update(team=args.team, server=servers, testcase=testcases, framework=args.framework)

    print(json.dumps(kwargs, indent=4))
    test_controller = TestController(kwargs)
    test_controller.start()
