import logging

logging.basicConfig(
    level=logging.INFO, format="%(message)s - %(levelname)s - %(module)s - %(lineno)d"
)


def __get_message(message: str, indent_level: int):
    if indent_level < 1:
        indent_level = 1

    new_line = "\n" if indent_level == 1 else ""
    indent = "  " * (indent_level - 1)
    prefix = "[" + ("*" * indent_level) + "]"

    return new_line + indent + prefix + message


def debug(message: str, indent_level: int = 1):
    logging.debug(__get_message(message, indent_level))


def info(message: str, indent_level: int = 1):
    logging.info(__get_message(message, indent_level))


def warning(message: str, indent_level: int = 1):
    logging.warning(__get_message(message, indent_level))


def error(message: str, indent_level: int = 1):
    logging.error(__get_message(message, indent_level))


def exception(message: str, indent_level: int = 1):
    logging.exception(__get_message(message, indent_level))


def critical(message: str, indent_level: int = 1):
    logging.critical(__get_message(message, indent_level))
