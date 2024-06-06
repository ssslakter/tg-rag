from pathlib import Path
from datetime import date
import logging as l


DEF_FMT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def init_logger(name: str = None, level=l.INFO, format: str = None, handlers: list = None, logs_dir='./logs'):
    '''Initializes a logger, adds handlers and sets the format. If logs_dir is provided, a file handler is added to the logger.'''
    if handlers is None: handlers = []
    handlers.append(l.StreamHandler())
    if logs_dir:
        p = Path(logs_dir) / f'{date.today()}.log'
        p.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(l.FileHandler(p))
    if format is None: format = DEF_FMT
    log_fmt = l.Formatter(format, datefmt='%Y-%m-%d %H:%M:%S')
    log = l.getLogger(name)
    log.setLevel(level)
    log.handlers.clear()
    for h in handlers: h.setFormatter(log_fmt); log.addHandler(h)
