import os
import logging

class RequireSQLQueryLogPath (logging.Filter):
    def filter (this, record):
        return 'SQL_QUERY_LOG_PATH' in os.environ
