import boto3
import datetime
import gzip
import json
import logging
import os
import os.path
import shutil
import subprocess
import tempfile
import time
import traceback
import zipfile

from multiprocessing.dummy import Pool
from pythonjsonlogger import jsonlogger
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from scrapy.spiderloader import SpiderLoader
from scrapy import signals

upload_to_s3 = False

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
    _, output_log = tempfile.mkstemp('.log')
    _, output_results = tempfile.mkstemp('.geojson')

    logger.warning("Scrapy crawl for %s", spider_name)

    start = time.time()
    result = subprocess.run([
        'scrapy', 'crawl',
        '--output', output_results,
        '--output-format', 'ndgeojson',
        '--logfile', output_log,
        '--loglevel', 'INFO',
        '--set', 'TELNETCONSOLE_ENABLED', '0',
        '--set', 'CLOSESPIDER_TIMEOUT', '21600', # 6 hours
        spider_name
    ], env=os.environ.copy())
    elapsed = time.time() - start

    logger.warning("Scrapy crawl for %s exited code %s after %0.1f sec: %s", spider_name, result.returncode, elapsed, result.arg)

    return {
        'output_filename': output_results,
        'log_filename': output_log,
        'exit_code': result.returncode,
        'elapsed': elapsed,
        'spider_name': spider_name,
    }


def main():
    logger.warn("Loading project")

    s3_bucket = os.environ.get('S3_BUCKET')
    assert s3_bucket, "Please specify an S3_BUCKET environment variable"

    utcnow = datetime.datetime.utcnow()
    tstamp = utcnow.strftime('%F-%H-%M-%S')
    pool_size = 1

    settings = get_project_settings()
    spider_loader = SpiderLoader.from_settings(settings)
    spider_names = spider_loader.list()[45:50]

    pool = Pool(pool_size)
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
    if upload_to_s3:
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

    # Concatenate and zip the log files
    _, log_zip_filename = tempfile.mkstemp('.log.zip')
    with zipfile.ZipFile(log_zip_filename, 'w', compression=zipfile.ZIP_DEFLATED) as f_out:
        for r in results:
            log_filename = r.pop('log_filename')
            f_out.write(log_filename, os.path.join('logs', log_filename))

    # Post it to S3
    s3_log_key = '{}/all_logs.log.zip'.format(s3_key_prefix)
    if upload_to_s3:
        client.upload_file(
            log_zip_filename,
            s3_bucket,
            s3_log_key,
            ExtraArgs={
                'ACL': 'public-read',
                'ContentType': 'application/zip',
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
    if upload_to_s3:
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
    if upload_to_s3:
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
    if upload_to_s3:
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
