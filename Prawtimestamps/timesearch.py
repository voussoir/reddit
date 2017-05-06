import sys
import timesearch

status_code = timesearch.main(sys.argv[1:])
raise SystemExit(status_code)
