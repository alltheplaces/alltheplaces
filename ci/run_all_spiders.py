import boto3
import datetime
import gzip
import json
import os
import os.path
import shutil


if __name__ == '__main__':
    print("Loading project")

    s3_bucket = os.environ.get('S3_BUCKET')
    assert s3_bucket, "Please specify an S3_BUCKET environment variable"

    output_log = 'all_spiders.log'
    output_results = 'output.geojson'

    from scrapy.utils.project import get_project_settings
    from scrapy.crawler import CrawlerProcess
    from scrapy import signals
    settings = get_project_settings()

    settings.set('LOG_FILE', output_log)
    settings.set('LOG_LEVEL', 'ERROR')
    settings.set('TELNETCONSOLE_ENABLED', False)
    settings.set('FEED_URI', output_results)
    settings.set('FEED_FORMAT', 'ndgeojson')
    settings.get('ITEM_PIPELINES')['locations.pipelines.ApplySpiderNamePipeline'] = 100

    utcnow = datetime.datetime.utcnow()
    tstamp = utcnow.strftime('%F-%H-%M-%S')
    spider_stats = {}

    def spider_opened(spider):
        print("Spider %s opened" % spider.name)

    def spider_closed(spider):
        spider_stats[spider.name] = {
            'finish_reason': spider.crawler.stats.get_value('finish_reason'),
            'duration': (
                spider.crawler.stats.get_value('finish_time') -
                spider.crawler.stats.get_value('start_time')).total_seconds(),
            'item_scraped_count':
                spider.crawler.stats.get_value('item_scraped_count'),
        }

        print("Spider %s closed (%s) after %0.1f sec, %d items" % (
            spider.name,
            spider.crawler.stats.get_value('finish_reason'),
            (spider.crawler.stats.get_value('finish_time') -
                spider.crawler.stats.get_value('start_time')).total_seconds(),
            spider.crawler.stats.get_value('item_scraped_count') or 0,
        ))

    print("Starting to crawl")
    process = CrawlerProcess(settings)
    for spider_name in process.spider_loader.list():
        crawler = process.create_crawler(spider_name)
        crawler.signals.connect(spider_closed, signals.spider_closed)
        crawler.signals.connect(spider_opened, signals.spider_opened)
        process.crawl(crawler)
    process.start()
    print("Done crawling")

    client = boto3.client('s3')
    s3_key_prefix = "runs/{}".format(tstamp)

    # Gzip the output geojson
    with open(output_results, 'rb') as f_in:
        with gzip.open(output_results + '.gz', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    s3_output_size = os.path.getsize(output_results + '.gz')
    s3_output_size_mb = s3_output_size / 1024 / 1024

    # Post it to S3
    s3_output_key = '{}/{}.gz'.format(s3_key_prefix, output_results)
    client.upload_file(
        output_results + '.gz',
        s3_bucket,
        s3_output_key,
        ExtraArgs={
            'ACL': 'public-read',
            'ContentType': 'application/json',
            'ContentDisposition': 'attachment; filename="output-{}.geojson.gz"'.format(tstamp),
        }
    )

    print("Saved output to https://s3.amazonaws.com/{}/{}".format(s3_bucket, s3_output_key))

    # Gzip the log file
    with open(output_log, 'rb') as f_in:
        with gzip.open(output_log + '.gz', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    # Post it to S3
    s3_log_key = '{}/{}.gz'.format(s3_key_prefix, output_log)
    client.upload_file(
        output_log + '.gz',
        s3_bucket,
        s3_log_key,
        ExtraArgs={
            'ACL': 'public-read',
            'ContentType': 'text/plain; charset=utf-8',
            'ContentEncoding': 'gzip',
        }
    )

    print("Saved logfile to https://s3.amazonaws.com/{}/{}".format(s3_bucket, s3_log_key))

    metadata = {
        'spiders': spider_stats,
        'links': {
            'download_url': "https://s3.amazonaws.com/{}/{}".format(s3_bucket, s3_output_key),
            'log_url': "https://s3.amazonaws.com/{}/{}".format(s3_bucket, s3_log_key),
        }
    }

    with open('metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

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
    print("Saved metadata to https://s3.amazonaws.com/{}/{}".format(s3_bucket, s3_key))

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
    print("Saved metadata to https://s3.amazonaws.com/{}/{}".format(s3_bucket, s3_key))

    total_count = sum(
        filter(
            None,
            (s['item_scraped_count'] for s in spider_stats.values())
        )
    )
    template_content = {
        'download_url': 'https://s3.amazonaws.com/{}/{}'.format(s3_bucket, s3_output_key),
        'download_size': round(s3_output_size_mb, 1),
        'row_count': total_count,
        'spider_count': len(spider_stats),
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
    print("Saved embed to https://s3.amazonaws.com/{}/{}".format(s3_bucket, s3_key))
