from state_machine import StateMachine
from api.api import Api
if __name__ == "__main__":
    api = Api(api='http://localhost:8000')
    machine = StateMachine('config.json')
    
    try:
        machine.run()
    except KeyboardInterrupt:
        print('')
        machine.logger.info("Exiting...")
    finally:
        machine.disconnect()