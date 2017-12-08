from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess


if __name__ == '__main__':
    settings = get_project_settings()

    settings.set('LOG_FILE', 'all_spiders.log')
    settings.set('LOG_LEVEL', 'ERROR')
    settings.set('TELNETCONSOLE_ENABLED', False)
    settings.set('FEED_URI', 'output.ndgeojson')
    settings.set('FEED_FORMAT', 'ndgeojson')
    settings.get('ITEM_PIPELINES')['locations.pipelines.ApplySpiderNamePipeline'] = 100

    process = CrawlerProcess(settings)
    for spider_name in process.spider_loader.list():
        process.crawl(spider_name)
    process.start()
