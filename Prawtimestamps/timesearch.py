import logging
handler = logging.StreamHandler()
log_format = '{levelname}:timesearch.{module}.{funcName}: {message}'
handler.setFormatter(logging.Formatter(log_format, style='{'))
logging.getLogger().addHandler(handler)


import sys
import timesearch

status_code = timesearch.main(sys.argv[1:])
raise SystemExit(status_code)
