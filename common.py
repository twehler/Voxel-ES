import logging

def logging_setup():
    logging.basicConfig(
        filename="Simulation.log",
        level = logging.DEBUG,
        format='%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s'
        )

logging_setup()

