from scrapy.crawler import Crawler

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.count_categories import CountCategoriesPipeline
from locations.spiders.greggs_gb import GreggsGBSpider


def get_objects():
    class Spider(object):
        pass

    spider = Spider()
    crawler = Crawler(GreggsGBSpider)
    spider.crawler = crawler
    crawler._apply_settings()
    return Feature(), CountCategoriesPipeline(), spider


def test_missing():
    item, pipeline, spider = get_objects()
    pipeline.process_item(item, spider)
    assert spider.crawler.stats.get_value("atp/category/missing", 0) == 1
    assert spider.crawler.stats.get_value("atp/category/multiple", 0) == 0


def test_category():
    item, pipeline, spider = get_objects()
    apply_category(Categories.SHOP_FLORIST, item)
    pipeline.process_item(item, spider)
    assert spider.crawler.stats.get_value("atp/category/shop/florist", 0) == 1
    assert spider.crawler.stats.get_value("atp/category/missing", 0) == 0
    assert spider.crawler.stats.get_value("atp/category/multiple", 0) == 0


def test_multiple():
    item, pipeline, spider = get_objects()
    apply_category(Categories.BICYCLE_RENTAL, item)
    apply_category(Categories.SHOP_FLORIST, item)
    pipeline.process_item(item, spider)
    assert spider.crawler.stats.get_value("atp/category/amenity/bicycle_rental", 0) == 1
    assert spider.crawler.stats.get_value("atp/category/shop/florist", 0) == 0
    assert spider.crawler.stats.get_value("atp/category/missing", 0) == 0
    assert spider.crawler.stats.get_value("atp/category/multiple", 0) == 1
