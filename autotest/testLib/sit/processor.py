from autotest.testLib.base import Base

class Processor(Base):
    '''
    description: this class is test library for processor
    author: yuhanhou
    '''

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)
        self.local_register('test_demo_cpu2')



    def test_demo_cpu1(self, **kwargs):
        self.ping('127.0.0.1', max_time=120)
        self.logger.info('testing cpu1...')
        result = {'result':'pass'}
        return result


    def test_demo_cpu2(self, **kwargs):
        '''
        decription: this is a test of cpu2
        loader: shadow
        author: yuhanhou
        params: kwargs
        return:
        '''
        
        self.logger.info('testing cpu2...')
        result = {'result':'fail', 'reason':'cpu2 missing'}
        return result
