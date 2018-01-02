import boto3
import datetime
import gzip
import json
import logging
import multiprocessing
import os
import os.path
import shutil
import tempfile
import traceback

from pythonjsonlogger import jsonlogger
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from scrapy.spiderloader import SpiderLoader
from scrapy import signals

logger = logging.getLogger('atp')
ch = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(message)s %(process)s")
ch.setFormatter(formatter)
ch.setLevel(logging.INFO)
logger.addHandler(ch)

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

def run_one_spider(spider_name):
    try:
        settings = get_project_settings()

        _, output_log = tempfile.mkstemp('.log')
        _, output_results = tempfile.mkstemp('.geojson')

        settings.set('LOG_FILE', output_log)
        settings.set('LOG_LEVEL', 'INFO')
        settings.set('TELNETCONSOLE_ENABLED', False)
        settings.set('FEED_URI', output_results)
        settings.set('FEED_FORMAT', 'ndgeojson')

        def spider_opened(spider):
            logger.info("Spider %s opened, saving to %s", spider.name, output_results)

        def spider_closed(spider):
            logger.info("Spider %s closed (%s) after %0.1f sec, %d items",
                spider.name,
                spider.crawler.stats.get_value('finish_reason'),
                (spider.crawler.stats.get_value('finish_time') -
                    spider.crawler.stats.get_value('start_time')).total_seconds(),
                spider.crawler.stats.get_value('item_scraped_count') or 0,
            )

        process = CrawlerProcess(settings)
        crawler = process.create_crawler(spider_name)
        crawler.signals.connect(spider_closed, signals.spider_closed)
        crawler.signals.connect(spider_opened, signals.spider_opened)
        process.crawl(crawler)
        process.start()

        results = crawler.stats.spider_stats.get(spider_name)
        results['output_filename'] = output_results
        results['log_filename'] = output_log
        results['spider'] = spider_name
        return results
    except Exception as e:
        logger.exception("Exception in scraper process")


def main():
    logger.warn("Loading project")

    s3_bucket = os.environ.get('S3_BUCKET')
    assert s3_bucket, "Please specify an S3_BUCKET environment variable"

    utcnow = datetime.datetime.utcnow()
    tstamp = utcnow.strftime('%F-%H-%M-%S')
    pool_size = 12

    settings = get_project_settings()
    spider_loader = SpiderLoader.from_settings(settings)
    spider_names = spider_loader.list()

    pool = multiprocessing.Pool(pool_size, maxtasksperchild=1)
    logger.info("Starting to crawl %s spiders on %s processes", len(spider_names), pool_size)
    results = pool.imap_unordered(run_one_spider, spider_names)
    pool.close()
    pool.join()
    logger.info("Done crawling")

    # The imap_unordered call returns an iterator, so throw it in a list
    results = list(results)

    client = boto3.client('s3')
    s3_key_prefix = "runs/{}".format(tstamp)

    # Concatenate and gzip the output geojsons
    _, output_gz_filename = tempfile.mkstemp('.geojson.gz')
    with gzip.open(output_gz_filename, 'wb') as f_out:
        for r in results:
            with open(r.pop('output_filename'), 'rb') as f_in:
                shutil.copyfileobj(f_in, f_out)

    s3_output_size = os.path.getsize(output_gz_filename)
    s3_output_size_mb = s3_output_size / 1024 / 1024

    # Post it to S3
    s3_output_key = '{}/output.geojson.gz'.format(s3_key_prefix)
    client.upload_file(
        output_gz_filename,
        s3_bucket,
        s3_output_key,
        ExtraArgs={
            'ACL': 'public-read',
            'ContentType': 'application/json',
            'ContentDisposition': 'attachment; filename="output-{}.geojson.gz"'.format(tstamp),
        }
    )

    logger.warn("Saved output to https://s3.amazonaws.com/%s/%s", s3_bucket, s3_output_key)

    # Concatenate and gzip the log files
    _, log_gz_filename = tempfile.mkstemp('.log.gz')
    with gzip.open(log_gz_filename, 'wb') as f_out:
        for r in results:
            with open(r.pop('log_filename'), 'rb') as f_in:
                shutil.copyfileobj(f_in, f_out)

    # Post it to S3
    s3_log_key = '{}/all_logs.txt.gz'.format(s3_key_prefix)
    client.upload_file(
        log_gz_filename,
        s3_bucket,
        s3_log_key,
        ExtraArgs={
            'ACL': 'public-read',
            'ContentType': 'text/plain; charset=utf-8',
            'ContentEncoding': 'gzip',
        }
    )

    logger.warn("Saved logfile to https://s3.amazonaws.com/%s/%s", s3_bucket, s3_log_key)

    metadata = {
        'spiders': results,
        'links': {
            'download_url': "https://s3.amazonaws.com/{}/{}".format(s3_bucket, s3_output_key),
            'log_url': "https://s3.amazonaws.com/{}/{}".format(s3_bucket, s3_log_key),
        }
    }

    with open('metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2, default=json_serial)

    s3_key = '{}/metadata.json'.format(s3_key_prefix)
    client.upload_file(
        'metadata.json',
        s3_bucket,
        s3_key,
        ExtraArgs={
            'ACL': 'public-read',
            'ContentType': 'application/json; charset=utf-8',
        }
    )
    logger.warn("Saved metadata to https://s3.amazonaws.com/%s/%s", s3_bucket, s3_key)

    s3_key = 'runs/latest/metadata.json'
    client.upload_file(
        'metadata.json',
        s3_bucket,
        s3_key,
        ExtraArgs={
            'ACL': 'public-read',
            'ContentType': 'application/json; charset=utf-8',
        }
    )
    logger.warn("Saved metadata to https://s3.amazonaws.com/%s/%s", s3_bucket, s3_key)

    total_count = sum(
        filter(
            None,
            (s['item_scraped_count'] for s in results)
        )
    )
    template_content = {
        'download_url': 'https://s3.amazonaws.com/{}/{}'.format(s3_bucket, s3_output_key),
        'download_size': round(s3_output_size_mb, 1),
        'row_count': total_count,
        'spider_count': len(results),
        'updated_datetime': utcnow.replace(microsecond=0).isoformat(),
    }
    with open('info_embed.html', 'w') as f:
        f.write(
            "<html><body>"
            "<a href=\"{download_url}\">Download</a> "
            "({download_size} MB)<br/><small>{row_count:,} rows from "
            "{spider_count} spiders, updated {updated_datetime}Z</small>"
            "</body></html>\n".format(
                **template_content
            )
        )
    s3_key = 'runs/latest/info_embed.html'
    client.upload_file(
        'info_embed.html',
        s3_bucket,
        s3_key,
        ExtraArgs={
            'ACL': 'public-read',
            'ContentType': 'text/html; charset=utf-8',
        }
    )
    logger.warn("Saved embed to https://s3.amazonaws.com/%s/%s", s3_bucket, s3_key)


if __name__ == '__main__':
    main()
