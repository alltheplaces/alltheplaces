import logging
import os

from scrapy import logformatter


class DebugDuplicateLogFormatter(logformatter.LogFormatter):
    def dropped(self, item, exception, response, spider):
        return {
            "level": logging.DEBUG,
            "msg": "Dropped: %(exception)s" + os.linesep + "%(item)s",
            "args": {
                "exception": exception,
                "item": item,
            },
        }
