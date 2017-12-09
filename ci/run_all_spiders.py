from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from scrapy import signals


if __name__ == '__main__':
    settings = get_project_settings()

    settings.set('LOG_FILE', 'all_spiders.log')
    settings.set('LOG_LEVEL', 'ERROR')
    settings.set('TELNETCONSOLE_ENABLED', False)
    settings.set('FEED_URI', 'output.ndgeojson')
    settings.set('FEED_FORMAT', 'ndgeojson')
    settings.get('ITEM_PIPELINES')['locations.pipelines.ApplySpiderNamePipeline'] = 100

    def spider_opened(spider):
        print("Spider %s opened" % spider.name)

    def spider_closed(spider):
        print("Spider %s closed (%s) after %0.1f sec, %d items" % (
            spider.name,
            spider.crawler.stats.get_value('finish_reason'),
            (spider.crawler.stats.get_value('finish_time') -
                spider.crawler.stats.get_value('start_time')).total_seconds(),
            spider.crawler.stats.get_value('item_scraped_count'),
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
