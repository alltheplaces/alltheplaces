import json
import os
from datetime import datetime

from scrapy import Spider


def feed_uri_params(params, spider: Spider):
    job_data = json.loads(os.environ.get("JOB_DATA", "{}"))
    pending_time = (
        datetime.utcfromtimestamp(int(job_data.get("pending_time") / 1000))
        if "pending_time" in job_data
        else datetime.utcnow()
    )

    return {
        **params,
        "env": spider.settings.get("ENV"),
        "bucket": spider.settings.get("GCS_BUCKET"),
        "schedule_date": pending_time.strftime("%Y-%m-%d"),
        "spider_name": spider.name,
    }
