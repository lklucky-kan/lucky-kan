import testlink
import re
import os
from datetime import datetime
from common.other.log import Logger


class TestLinkManager():
    '''
    description: this class is used for testlink management including test result update, get testcase info, etc
    author: yuhanhou
    '''

    def __init__(self, **kwargs):
        '''
        description: init method
        params: kwargs, optional keywords params
                    server: testlink server ip:port or dns name
                    access_key: testlink api personal access key generated by testlink
                    logger: existing logger
                    project: project name on testlink, default is 'Test Repository'
        author: yuhanhou
        return: NA
        '''
        self.server = kwargs.get('server', '10.67.13.194:8888')
        self.access_key = kwargs.get('access_key', '0ff5eaf8e9eb30439bdb81c4feabcd53')
        self.url = 'http://' + self.server + '/testlink/lib/api/xmlrpc/v1/xmlrpc.php'
        self.logger = kwargs.get('logger', Logger(log_file='testlink.log'))
        # self.project = kwargs.get('project', 'Test Repository')
        self.api = testlink.TestlinkAPIClient(self.url, self.access_key)


    def update_testcase_result(self, result):
        '''
        description: update test result to testlink and attach the test detailed logs or reports
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
                        } ,
                        ...
                    
        return: result,  fail or success of this upload
        '''
        key_map = { #used for testlink result key map
            'pass':'p',
            'fail':'f',
            'block':'b'
        }

      
        case_result = key_map[result.get('result', 'fail')]
        testplan_id = self.get_testplan_id(result.get('project'), result.get('testplan'))
        case_id = result.get('case_id')
        timestamp = result.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M'))#'2015-09-18 14:33'
        logs = result.get('logs')
        
        #prepare kwargs for testlink api reportTCResult mehtod
        kwargs = {'timestamp':timestamp, 'guess':True, 'testcaseexternalid':case_id}
        
        if 'build' in result:
            kwargs['build'] = result.get('build')
        
        if 'platform' in result:
            kwargs['platformname'] = result.get('platform')

        if 'execduration' in result:
            kwargs['execduration'] = result.get('execduration')

        #tls.reportTCResult(None, '2', None, 'f', '', guess=True,
        #                        testcaseexternalid='tp-16', platformname='tp_sit_f1',
        #                        execduration=3.9, timestamp='2015-09-18 14:33')

        #update result to testlink:
        temp_list = self.api.reportTCResult(None, testplan_id, None, case_result, '', **kwargs)
        
        #temp_list:
        #[{'status': True, 'operation': 'reportTCResult', 'overwrite': False, 'message': 'Success!', 'id': 32}]
        testlink_result = temp_list.pop()
        if re.search('success', testlink_result.get('message', ''), re.I):
            self.logger.info('Update testcase ' + case_id + ' in testplan ' + result.get('testplan') + ' of project ' + result.get('project') + ' successfully!')
            testlink_result_id = testlink_result.get('id')
            
            #upload logs to testlink:
            for log in logs:
                self.api.uploadExecutionAttachment(log, testlink_result_id, os.path.basename(log), os.path.basename(log))
                self.logger.info('Attached ' + log + ' into testlink result.')
        else:
            self.logger.error('Failed to update result to testlink! testcase:' + case_id + ', testplan:' + testplan_id)
        


    def get_testplan_id(self, project_name, testplan_name):
        '''
        description: get testplan ID by project name and testplan name
        author: yuhanhou
        params: project_name, project name on testlink
                testplan_name, test plan name on testlink

        return: testplan id
        '''
        testplan_id = None

        try:
            temp_list = self.api.getTestPlanByName(project_name, testplan_name)
            # temp_list:
            # [{'id': '15058', 'testproject_id': '15053', 'notes': '', 'active': '1', 'is_open': '1', 'is_public': '0', 'api_key': 'cdd254128a5e6ef87ffcb2befd3fb7c3efbac1da76cb20b537ebfb6abeb5a462', 'name': 'daisy_plan1'}]
            testplan_info = temp_list.pop()
            testplan_id = testplan_info.get('id')

        except testlink.testlinkerrors.TLResponseError as err:
            self.logger.error(err)

        return testplan_id

 

if __name__ == '__main__':
    tlm = TestLinkManager(project='daisy_pro')


                            # 'result':'pass|fail|block'
                            # 'testplan': testplan name
                            # 'case_id': testcase external id
                            # 'timestamp': testing timestamp
                            # 'build': optional, default will upload to the latest build
                            # 'platform': if defined platform for this execution on testlink, \
                            #             this is needed.
                            # 'execduration': minutes(float), optional, duration time of this testcase
                            # 'logs': list of log files path
    results = [{'case_id':'daisy-1','result':'fail', 'testplan':'daisy_plan1', 'platform':'linux', 'logs':['D:\\sit\\????????????xx.txt', 'D:\\sit\\????????????.txt']}]

    tlm.update_testcase_result(results)
