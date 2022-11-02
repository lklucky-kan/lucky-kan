import json
import urllib3
import requests
from collections import defaultdict
from common.communication.session import Session

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Redfish(Session):
    """
    Redfish request/response container
    author: zhuangzhao
    e.g.
        server_info = self.options.get('server')
        res = RedfishRequest(url='redfish/v1', method='GET')
        redfish = RedfishLan(ip=server_info.get('bmc_ip'), user=server_info.get('bmc_user'),
                             password=server_info.get('bmc_password'))
        redfish.cmd(res)
    """

    def __init__(self, **kwargs):
        Session.__init__(self, **kwargs)
        self.product_name = None
        self.port = 443

    def cmd(self, url, **kwargs):
        # Limitation: This Redfish library can not establish session to Redfish service, it uses basic-auth only

        method = kwargs.get('method')
        # body = kwargs.get('body', default=None)
        body = None
        headers = None
        # headers = kwargs.get('headers', default=None)
        files = None
        if url.startswith('/redfish/v1'):
            url = url[1:]
        # Clear data for the already sent redfish request
        full_url = f'https://{self.ip}:{self.port}/{url}'
        self.logger.info(f'Sending Redfish request {full_url}, method {method}')
        if headers:
            self.logger.info('headers:')
            self.logger.info(headers)
        if body:
            self.logger.info('body:')
            self.logger.info(body)

        try:
            if method == 'GET':
                res = requests.get(full_url, auth=(self.user, self.password),
                                   headers=headers, verify=False, timeout=60)
            elif method == 'POST':
                res = requests.post(full_url, data=body, auth=(self.user, self.password),
                                    headers=headers, files=files, verify=False)
            elif method == 'PATCH':
                res = requests.patch(full_url, data=body, auth=(self.user, self.password),
                                     headers=headers, verify=False)
            elif method == 'PUT':
                res = requests.put(full_url, data=body, auth=(self.user, self.password),
                                   headers=headers, verify=False)
            elif method == 'DELETE':
                res = requests.delete(full_url, auth=(self.user, self.password), verify=False)
            else:
                raise ValueError(f'{method} is NOT a valid Redfish operation')
        except Exception as e:
            self.logger.error(e)
            return 1

        try:
            _jsons = res.json()
            self.logger.info('\n' + json.dumps(_jsons, sort_keys=True, indent=4))
            # To prevent the test script from raising Key Error exception
            # Access a non-exist property will return string "Property Not Exist'
            jsons = defaultdict(lambda: 'Property Not Exist', _jsons)
        except json.decoder.JSONDecodeError:
            _jsons = None
            jsons = None
            self.logger.error(f'Response is not a valid JSON string')
        full_url = res.url
        status_code = res.status_code
        elapsed = res.elapsed
        return _jsons


