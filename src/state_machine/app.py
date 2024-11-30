from state_machine import StateMachine

if __name__ == "__main__":
    machine = StateMachine('config.json')
    try:
        machine.run()
    except KeyboardInterrupt:
        print('')
        machine.logger.info("Exiting...")
    finally:
        machine.disconnect()