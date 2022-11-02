from common.other.log import Logger

class Session():
    '''
    This is a session class to support remote connection with different systems
    author: yuhanhou
    '''

    def __init__(self, **kwargs):
        self.ip = kwargs.get('ip')
        self.user = kwargs.get('user')
        self.password = str(kwargs.get('password'))
        self.port = kwargs.get('port')
        self.timeout = kwargs.get('timeout', 600)
        self.prompt = kwargs.get('prompt', '')
        self.logger = kwargs.get('logger')
        self.session = kwargs.get('session')

        # 如果没有指定logger对象， 则根据kwargs参数创建logger对象
        if not self.logger:
            self.logger = Logger(**kwargs)

    

    def open(self):
        pass

    def cmd(self, cmdline, **kwargs):
        pass
        return ''


    def close(self):
        pass
