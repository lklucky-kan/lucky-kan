'''
description: this is a shadow caller on DUT to start standalone test case
author: yuhanhou
'''
import re, os
import argparse
import sys, platform
sys.path.insert(0, '..')
from importlib import import_module
from autotest.testLib.factory import TestFactory
from common.file.csv_parser import CSV_Parser

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
    parser = argparse.ArgumentParser(description='local case runner which is running on Server locally!')
    parser.add_argument('-c','--profile', default='NA', help='the path of profile')
    parser.add_argument('-f','--framework', default='tea', help='framework of the test, robot or selenium or tea, default is tea')
    parser.add_argument('-t','--team', default='sit', help='team of the test case. sit, bmc supported')    
    parser.add_argument('-s','--server',  help='-s ip=xxip,user=xxuser,password=xxx,bmc_ip=xxbmc,bmc_user=yyuser,bmc_password=bpwd -s ... -s ...')
    parser.add_argument('-i', '--testcase', required=True, help='-i name=testcase1,lib=xx,case_func=fuc1,loop=2,tool=xxtool')
    parser.add_argument('-o', '--optional', action='append', help='optional keywords args like: -o k1=v1 -o k2=v2 -o flag')
    args = parser.parse_args()


    kwargs = {'run_mode':'local'} #this mode is used in test/testLib/base.py to distinguish log collection with remote mode
    
    tea_path = ''
    scripts_root_path = ''
    local_runner_abspath = os.path.abspath(__file__) #the current path of local_case_runner.py located.
    
    match = re.search(r'((^\S+)\Stea)', local_runner_abspath)
    if match:
        tea_path = match.group(1)
        scripts_root_path = match.group(2)

    if args.testcase:
       
        tmp_list = re.split(r',', args.testcase.strip())
        kwargs['testcase'] = parse_kwPairs2dict(tmp_list)
        # testcases = args.include

    #parse server in test dict info into servers list:
    if args.server:
        tmp_list = re.split(r',', args.server.strip())
        kwargs['server'] = parse_kwPairs2dict(tmp_list)

    if 'server' in kwargs: 
        kwargs['server'].update(protocol='local')
    else:
        kwargs['server'] = {'protocol':'local'}
    
    kwargs['server']['tea_path'] = tea_path
    kwargs['server']['scripts_root_path'] = scripts_root_path
    
    if 'ip' not in kwargs['server']:
        kwargs['server']['ip'] = 'localhost'

    if 'os' not in kwargs['server']:
        os_name = platform.platform()
        kwargs['server'].update(os=os_name)
    

    #change standalone script mod on linux:
    if not re.search('win', kwargs['server'].get('os'), re.I):
        os.system('chmod 755 -R ' + tea_path)

    if args.optional:
        kwargs.update(parse_kwPairs2dict(args.optional))
 

    case_info = kwargs.get('testcase')
    case = None

    if 'lib' not in case_info:
        csv = CSV_Parser(separator=r'\s*,\s*')

        cur_path = os.path.abspath('.')
        tea_path = ''
        match = re.search(r'(\S+tea)', cur_path)
        if match:
            tea_path = match.group(1)

        mapping_file = os.path.join(tea_path, 'autotest', 'profile', 'case_mapping')
        case_map = {items[0]:items[1] for items in csv.read(mapping_file, data_s='list')}

        testlink_casename = case_info.get('fullname')
        case_name = case_info.get('name', case_map.get(testlink_casename))
        if case_name == None:
            raise Exception('no testcase name is provided! Please check the cli params and the test/profile/case_mapping file.')

        lib, func = TestFactory.lookup_case_lib(case_name, args.team, args.framework)
        case_info.update(lib=lib, case_func=func)  
        case = TestFactory.create_testcase(lib, **kwargs)
    else:    
    #'test.testLib.sit.processor.Processor'
        lib_info = kwargs.get('testcase').get('lib')
        tmp_list = lib_info.split('.')
        #debug
        print(tmp_list)

        cls_name = tmp_list.pop()
        mod_name = '.'.join(tmp_list)
        
        imp_mod = import_module(mod_name)
        case_cls = getattr(imp_mod, cls_name)

        case = case_cls(**kwargs)

    case.test()
    
