import os
from logging import (ERROR, INFO, WARN, FileHandler, Formatter, Logger,
                     basicConfig, getLogger)


def log_config() -> Logger:
    formatter_str = '%(asctime)s [%(levelname)s] %(name)s (%(lineno)s): %(message)s'
    formatter = Formatter(formatter_str)
    basicConfig(format=formatter_str)

    log = getLogger('pytonisa')
    ocrmypdf_log = getLogger('ocrmypdf')
    pdfminer_log = getLogger('pdfminer')

    try:
        os.mkdir('logs')
    except:
        pass
    info_file = FileHandler('logs/infos.log')
    info_file.setLevel(INFO)
    info_file.setFormatter(formatter)
    warning_file = FileHandler('logs/warnings.log')
    warning_file.setLevel(WARN)
    warning_file.setFormatter(formatter)
    errors_file = FileHandler('logs/errors.log')
    errors_file.setLevel(ERROR)
    errors_file.setFormatter(formatter)

    log.setLevel(INFO)
    log.addHandler(info_file)
    log.addHandler(warning_file)
    log.addHandler(errors_file)
    ocrmypdf_log.setLevel(WARN)
    ocrmypdf_log.addHandler(warning_file)
    ocrmypdf_log.addHandler(errors_file)
    pdfminer_log.setLevel(ERROR)
    pdfminer_log.addHandler(errors_file)

    return log


log: Logger = log_config()
