import logging

def initialize_logging(name: str) -> logging.Logger:
    """
    Initialize logging configuration to log to both a file and the console.
    """

    # Create a logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create handlers
    file_handler = logging.FileHandler('cbio_tools.log')
    console_handler = logging.StreamHandler()

    # Set level for handlers
    file_handler.setLevel(logging.INFO)
    console_handler.setLevel(logging.INFO)

    # Create a logging format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(name)s - %(funcName)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger