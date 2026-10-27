
import logging

def init_logger(debug: bool) -> logging.Logger:
    """
    Initialize a logger with the specified logging level and output to a file.

    Args:
        debug: A boolean indicating whether to set the logging level to DEBUG or WARNING.

    Returns:
        A logging.Logger object with the specified logging level and file output.
    """

    # Determine the logging level based on the "debug" flag.
    loggingLevel = logging.DEBUG if debug else logging.WARNING

    # Configure logging with the specified logging level and format.
    logging.basicConfig(level=loggingLevel, format='%(asctime)s - %(levelname)s - %(message)s')

    # Get the root logger.
    logger = logging.getLogger()

    # Set up a file handler to write log messages to a file.
    file_handler = logging.FileHandler('prepare_clinical_data.log')
    file_handler.setLevel(loggingLevel)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Return the logger object.
    return logger

init_logger(False)

logging.debug("Hello")