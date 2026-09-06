import logging
import json
import time
import requests

# A trial POST is retried with the SAME body, so the same event_id, which is what
# makes the retry a replay the backend can recognise instead of a second trial.
TRIAL_POST_ATTEMPTS = 3
TRIAL_POST_INTERVAL = 5  # seconds


class Api:
    def __init__(self, api:str='http://localhost:8000',logger:logging.Logger=None):
        self.api = api
        self.logger = logger
        pass

    @staticmethod
    def _trial_payload(deflection_sensors_values: dict, recovery: float, run=None, event_id=None):
        """The legacy body, plus the run/stage identity when the backend supplied one.

        `recovery` is the recovery_time config constant, not a measurement - see
        docs/labos-airtable/evidence/firmware-production-runtime-contract-2026-08-31.md.
        The `run` and `event_id` keys are omitted entirely when absent, so a pre-MF
        backend receives byte-for-byte the body it receives today.
        """
        payload = {
            'deflections': [
                {
                    "deflection_gauge": i,
                    "max_deflection": deflection_sensors_values[i]['max_value'],
                    "permanent_deflection": deflection_sensors_values[i]['permanent_value'],
                    "recovery": recovery
                } for i in deflection_sensors_values
            ]
        }
        if event_id:
            payload['event_id'] = event_id
        if run:
            payload['run'] = run
        return payload

    def _post_trial(self, url: str, payload: dict):
        """POST a trial, retrying transport failures with an unchanged body.

        Raises the last exception once the attempts are spent: a lost trial has to
        stay loud. Missing telemetry must never read as a completed stage.
        """
        last_error = None
        for attempt in range(1, TRIAL_POST_ATTEMPTS + 1):
            try:
                res = requests.post(url, json=payload, timeout=30)
                res.raise_for_status()
                body = res.json()
                if self.logger:
                    self.logger.info(body)
                return body
            except Exception as e:
                last_error = e
                if self.logger:
                    self.logger.warning(
                        f"Trial POST attempt {attempt}/{TRIAL_POST_ATTEMPTS} to {url} failed: {e}"
                    )
                if attempt < TRIAL_POST_ATTEMPTS:
                    time.sleep(TRIAL_POST_INTERVAL)
        if self.logger:
            self.logger.error(
                f"Trial POST to {url} failed after {TRIAL_POST_ATTEMPTS} attempts "
                f"(event_id={payload.get('event_id')}): {last_error}"
            )
        raise last_error


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

    def finish_static_test(self, project_id: str, static_test_index:str, deflection_sensors_values: dict, recovery: float, run=None, event_id=None):
        return self._post_trial(
            f'{self.api}/projects/{project_id}/static_tests/{static_test_index}/trials',
            self._trial_payload(deflection_sensors_values, recovery, run, event_id),
        )


    def start_cyclic_test(self, project_id: str, test_id:str):
        res = requests.put(f'{self.api}/projects/{project_id}/cyclic_tests/{test_id}/start')
        if self.logger:
            self.logger.info(res.json())
        return res.json()



    def finish_cyclic_test(self, project_id: str, test_index:str, deflection_sensors_values: dict, recovery: float, run=None, event_id=None):
        return self._post_trial(
            f'{self.api}/projects/{project_id}/cyclic-tests/{test_index}/trials',
            self._trial_payload(deflection_sensors_values, recovery, run, event_id),
        )


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

