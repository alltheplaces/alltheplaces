import sys

from scrapy import Spider
from scrapy.signals import spider_opened

S_ATP_AGG = "S_ATP_AGGREGATORS"
S_ATP_BRANDS = "S_ATP_BRANDS"
S_ATP_GOV = "S_ATP_GOVERNMENTS"
S_ATP_INFRA = "S_ATP_INFRASTRUCTURE"
S_ATP_ADDRESSES = "S_ATP_ADDRESSES"
UNKNOWN_LINEAGE = "S_?"


def spider_class_to_lineage(spider: Spider) -> str:
    """
    Provide an indication of the origin of the spider.
    :param spider: the spider
    :return: an indication of the origin the spider
    """
    return spider_path_to_lineage(sys.modules[spider.__module__].__file__)


def spider_path_to_lineage(file_path: str) -> str:
    """
    Provide an indication of the origin of the spider.
    :param file_path: the location of the spider on the file system
    :return: an indication of the origin the spider
    """
    if "locations/government_spiders/" in file_path:
        return S_ATP_GOV
    elif "locations/aggregator_spiders/" in file_path:
        return S_ATP_AGG
    elif "locations/infrastructure_spiders/" in file_path:
        return S_ATP_INFRA
    elif "locations/address_spiders/" in file_path:
        return S_ATP_ADDRESSES
    elif "locations/spiders/" in file_path:
        return S_ATP_BRANDS
    else:
        return UNKNOWN_LINEAGE


class AddLineageExtension:

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls()
        crawler.signals.connect(ext.spider_opened, signal=spider_opened)
        return ext

    def spider_opened(self, spider: Spider):
        spider.crawler.stats.set_value("atp/lineage", spider_class_to_lineage(spider))
