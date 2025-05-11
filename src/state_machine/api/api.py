import logging
import json
import requests
class Api:
    def __init__(self, api:str='http://localhost:8000',logger:logging.Logger=None):
        self.api = api
        self.logger = logger
        pass
    
    def get_static_test(self, project_id: str, test_index: str):
        res = requests.get(f'{self.api}/projects/{project_id}/static-tests/{test_index}')
        if self.logger:
            self.logger.info(res.json())
        return res.json()
    
    def get_device(self, id: str):
        res = requests.get(f'{self.api}/devices/{id}')
        if self.logger:
            self.logger.info(res.json())
        return res.json()
        
    def get_next_cyclic_test(self, id: str):
        res = requests.get(f'{self.api}/projects/{id}/next-cyclic-test')
        if self.logger:
            self.logger.info(res.json())
        return res.json()

    def finish_static_test(self, project_id: str, test_id:str):
        res = requests.put(f'{self.api}/projects/{project_id}/static_tests/{test_id}/finish')
        if self.logger:
            self.logger.info(res.json())
        return res.json()


    def start_cyclic_test(self, project_id: str, test_id:str):
        res = requests.put(f'{self.api}/projects/{project_id}/cyclic_tests/{test_id}/start')
        if self.logger:
            self.logger.info(res.json())
        return res.json()



    def finish_cyclic_test(self, project_id: str, test_id:str):
        res = requests.put(f'{self.api}/projects/{project_id}/cyclic_tests/{test_id}/finish')
        if self.logger:
            self.logger.info(res.json())
        return res.json()


    def reset_cyclic_test(self, project_id: str, test_id:str):
        res = requests.put(f'{self.api}/projects/{project_id}/cyclic_tests/{test_id}/reset')
        if self.logger:
            self.logger.info(res.json())
        return res.json()
        
    def update_cyclic_test(self, project_id: str, test_id:str, current_cycle: int):
        res = requests.put(
            f'{self.api}/projects/{project_id}/cyclic_tests/{test_id}/update_status',
            data=json.dumps({
                    'current_cycle': current_cycle,
            }),
        )

        return res.json()

