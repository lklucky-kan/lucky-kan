from autotest.testLib.base import Base
import time
import os
import re
import datetime


class StressCycle(Base):
    '''
    description: this class is test library for stress cycle
    author: zhuangzhao
    '''

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)
        self.start_time = datetime.datetime.now()
        self.end_time = None
        self.result = {'result': 'pass', 'reason': []}
        self.server_info = self.options.get('server')
        self.server_obj = self.get_obj(self.server_info.get('ip'))
        self.ps_len = 0

    def get_error_log(self, path, file):
        """
        :param file:  file is log
        :param path : Collect the specified file to the error log directory
        """
        src_log_path = self.server_obj.local_log_path + self.server_obj.path_sep + path
        error_log = 'error_log'
        des_log_path = self.server_obj.local_log_path + self.server_obj.path_sep + error_log
        out = self.server_obj.cmd('ls -l ' + src_log_path + ' --color=never', return_list=False)
        if re.search(file, out, re.I):
            self.server_obj.raw_copy(src_log_path + file, des_log_path)
        else:
            print('no such %s' % file)

    def isprocesses(self, processes_name, ran=False, runtime=None):
        """
        :param processes_name: Processes that need to be checked
        :param ran: Select execution status
        :param processes: Checks whether the child process is in progress
        :param runtime: The time the script needs to run
        """
        output = self.server_obj.cmd('ps -ef |grep %s' % processes_name)
        if ran == 'check':
            self.end_time = datetime.datetime.now()
            if len(output) < self.ps_len + 1:
                self.runtime = (self.end_time - self.start_time).seconds
                if self.runtime > int(runtime):
                    print('---- %s is over ----- ' % processes_name)
                else:
                    print('---- %s is failed ----- ' % processes_name)
                    self.result['result'] = 'Fail'
                    self.result['reason'].append('%s is Fail, ' % processes_name)
                return 0
            else:
                return 1
        else:
            if len(output) < self.ps_len + 1:
                self.server_obj.cmd('pkill -f Stress')
            else:
                print('%s is running' % processes_name)

    def doctor(self, log_file):
        output = self.server_obj.cmd('cat %s' % log_file)
        for info in output:
            check_info = re.findall('Check.*', info, re.M)
            if not check_info:
                continue
            if 'PASS' in check_info[0]:
                pass
            else:
                self.result['result'] = 'Fail'
                self.result['reason'].append('please check error_log, ')
                break

    def test_stresscycle(self):
        value_list = ['sata', 'nvme', 'ocssd']
        self.server_obj.cmd('chmod 755 standalone/SIT-Storage_log_collect/storage_log_collect.sh')
        for value in value_list:
            output = self.server_obj.run_script('standalone/SIT-Storage_log_collect/storage_log_collect.sh',
                                                opts='-c %s' % value)
            if 'cannot' in output:
                print('get %s info fail' % value)
            else:
                print('get %s info' % value)
        self.server_obj.cmd('pkill -f Stress')
        print('kill Stress processes')
        output = self.server_obj.cmd('ps -ef |grep %s' % 'StressMonitor.py')
        self.ps_len = len(output)
        self.server_obj.cmd('chmod 755 standalone/SIT-LogFilter/LogFilterTool/LogFilterTool.py')
        output = self.server_obj.run_script('standalone/SIT-LogFilter/LogFilterTool/LogFilterTool.py', opts='--before ',
                                            program='python3')
        if 'Clear' in output:
            print(
                'Clear sel/sel_vlist/sdr/pci/dmesg/messages/mcelog/errors/moc_messages/filter_messages log before test begin.')
        else:
            raise Exception(output)
        try:
            run_time = self.options.get('time')
        except:
            run_time = 'None'
        if run_time:
            stress_opt = self.options.get('stress_opt',' ') + f' -t {run_time}'
            monitor_opt = self.options.get('monitor_opt') + f' -t {run_time}'
        else:
            stress_opt = self.options.get('stress_opt',' ')
            monitor_opt = self.options.get('monitor_opt')
        output = self.server_obj.run_script('standalone/SIT-Stress-Monitor/StressMonitor.py', opts=monitor_opt,
                                            bkground=True, name='Monitor', program='python3')
        time.sleep(5)
        self.isprocesses('StressMonitor.py')
        output = self.server_obj.run_script('standalone/SIT-Stress-CycleTest/stressCycle.py', opts=stress_opt,
                                   name='StressCycle', bkground=True, program='python3')
        time.sleep(5)
        print('test is runnig')
        print('Check whether each tool is executed ! ')
        monitor_thread, iperf_thread, fio_thread, mem_thread, cpu_thread = 1, 1, 1, 1, 1
        while monitor_thread == 1 :
            if monitor_thread == 1:
                monitor_thread = self.isprocesses('StressMonitor.py', ran='check', runtime=run_time)
            if monitor_thread == 0 and mem_thread == 0 and fio_thread == 0:
                break
            if iperf_thread == 1:
                if 'asip' in stress_opt:
                    iperf_thread = self.isprocesses('iperf', ran='check', runtime=run_time)
            if mem_thread == 1:
                mem_thread = self.isprocesses('"stress --vm "', ran='check', runtime=run_time)
            if fio_thread == 1:
                fio_thread = self.isprocesses('fio', ran='check', runtime=run_time)
            if cpu_thread == 1:
                cpu_thread = self.isprocesses('"stress -c"', ran='check', runtime=run_time)
            time.sleep(30)
        output = self.server_obj.run_script('standalone/SIT-LogFilter/LogFilterTool/LogFilterTool.py', opts='--after')
        for value in value_list:
            output = self.server_obj.run_script(
                'standalone/SIT-Storage_log_collect/storage_%s_log/storage_log_collect.sh' % value,
                opts='-c %s' % value, name=value)
            if 'cannot' in output:
                print('check %s info is faile . ' % value)
        
            elif 'pass' in output or 'Pass' in output:
                print('checking  %s info ' % value)
            else:
                print('check %s info is faile . ' % value)
        report_path = self.server_obj.tea_path + self.server_obj.path_sep + 'standalone/SIT-Storage_log_collect/reports'
        out = self.server_obj.cmd('ls -l ' + report_path + ' --color=never', return_list=False)
        self.server_obj.cmd('rm -rf %s ' % report_path)
        if re.search('no such', out, re.I):
            self.server_obj.cmd('mkdir -p ' + report_path)
        output = self.server_obj.cmd(
            'cd %s ;  mv standalone/SIT-Storage_log_collect/*_log  standalone/SIT-Storage_log_collect/reports ' % (self.server_obj.tea_path + self.server_obj.path_sep))
        self.collect_original_script_logs('SIT-Stress-Monitor')
        self.collect_original_script_logs('SIT-Stress-CycleTest')
        self.collect_original_script_logs('SIT-LogFilter/LogFilterTool')
        self.collect_original_script_logs('SIT-Storage_log_collect')
        self.get_error_log('SIT-Stress-Monitor/reports/', 'system_errors.log')
        self.get_error_log('SIT-LogFilter/LogFilterTool/reports/', 'errors.log')
        self.get_error_log('SIT-Stress-Monitor/reports/', 'lspci_error.log')
        self.get_error_log('SIT-Stress-Monitor/reports/', 'StressMonitor.log')
        output = self.server_obj.cmd('ls ' + self.server_obj.local_log_path + self.server_obj.path_sep + 'error_log')
        for path in output:
            path = self.server_obj.local_log_path + self.server_obj.path_sep + 'error_log' + self.server_obj.path_sep + path
            self.doctor(path)
        if self.result['result'] == 'Fail':
            error_info = [str(i) for i in set(self.result['reason'])]
            error_info = ''.join(error_info)
            self.result['reason'] = error_info
        else:
            self.result['reason'] = 'test is successful !'
        return self.result
