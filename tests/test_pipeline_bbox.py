from scrapy.utils.test import get_crawler

from locations.items import Feature
from locations.pipelines.bbox_calculator import BboxCalculator
from locations.spiders.greggs_gb import GreggsGBSpider


def test_bbox():
    pipeline = BboxCalculator()
    spider = GreggsGBSpider()
    spider.crawler = get_crawler()
    pipeline.process_item(Feature(lat=50.7490509, lon=-1.5698471), spider)
    pipeline.process_item(Feature(lat=50.5817046, lon=-1.0837289), spider)
    assert spider.crawler.stats.get_value("atp/bbox/lat_nw") == 50.5817046
    assert spider.crawler.stats.get_value("atp/bbox/lat_se") == 50.7490509
    assert spider.crawler.stats.get_value("atp/bbox/lon_nw") == -1.5698471
    assert spider.crawler.stats.get_value("atp/bbox/lon_se") == -1.0837289
