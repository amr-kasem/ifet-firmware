import logging
import requests
class Api:
    def __init__(self, api:str='http://localhost:8000',logger:logging.Logger | None = None):
        self.api = api
        self.logger = logger
        pass
    
    def get_static_test(self, id: str):
        res = requests.get(f'{self.api}/static-tests/{id}')
        if self.logger:
            self.logger.info(res)