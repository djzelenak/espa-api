import os
import sys
import logging

from logging import StreamHandler, FileHandler
from logging import Formatter
from logging.handlers import SMTPHandler
from api.providers.configuration.configuration_provider import ConfigurationProvider

config = ConfigurationProvider()

if config.mode not in ('tst', 'dev'):
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("passlib.registry").setLevel(logging.WARNING)
else:
    logging.getLogger('suds.client').setLevel(logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.DEBUG)

LOG_FORMAT = ("%(asctime)s [%(levelname)s]: %(message)s in %(pathname)s:%(lineno)d")

ilogger = logging.getLogger("api")
ilogger.setLevel(logging.DEBUG)

espa_log_dir = os.getenv('ESPA_LOG_DIR')
if espa_log_dir and not os.getenv('ESPA_LOG_STDOUT'):
    ih = FileHandler(os.path.join(espa_log_dir, 'espa-api-info.log'))
else:
    ih = StreamHandler(stream=sys.stdout)
eh = SMTPHandler(mailhost='localhost', fromaddr=config.get('apiemailsender'), toaddrs=config.get('ESPA_API_EMAIL_RECEIVE').split(','), subject='ESPA API ERROR')

if config.mode not in ('tst', 'dev'):
    ih.setLevel(logging.INFO)
else:
    ih.setLevel(logging.DEBUG)
eh.setLevel(logging.CRITICAL)

for handler in [ih, eh]:
    ilogger.addHandler(handler)

    if isinstance(handler, logging.StreamHandler):
        handler.setFormatter(Formatter(LOG_FORMAT))

