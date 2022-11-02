
from common.other.log import Logger
from common.infrastructure.sm.bmc import BMC
from autotest.testLib.base import Base


class RedfishTest(Base):

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)

    def test_redfish_lan(self):
        server_info = self.options.get('server')
        server_obj = self.get_obj(server_info.get('ip'))
        self.logger.info('set always-off policy on DUT...')
        bmc_ip = server_info.get('bmc_ip')        
        bmc_obj = self.get_obj(bmc_ip,protocol='redfish')
        bmc_obj.cmd('redfish/v1', method='GET'  )
        return {}
