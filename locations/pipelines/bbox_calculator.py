from scrapy import Spider

from locations.items import Feature, get_lat_lon


class BboxCalculator:

    def process_item(self, item: Feature, spider: Spider):
        if coords := get_lat_lon(item):
            spider.crawler.stats.max_value("atp/bbox/lat_max", coords[0])
            spider.crawler.stats.min_value("atp/bbox/lat_min", coords[0])
            spider.crawler.stats.max_value("atp/bbox/lon_max", coords[1])
            spider.crawler.stats.min_value("atp/bbox/lon_min", coords[1])
        return item
