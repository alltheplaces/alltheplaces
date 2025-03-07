import sys
from enum import Enum

from scrapy import Spider
from scrapy.signals import spider_opened


class Lineage(Enum):
    S_ATP_AGG = "S_ATP_AGGREGATOR"
    S_ATP_BRANDS = "S_ATP_BRANDS"
    S_ATP_GOV = "S_ATP_GOVERNMENT"
    S_ATP_INFRA = "S_ATP_INFRASTRUCTURE"
    S_ATP_ADDRESSES = "S_ATP_ADDRESSES"
    UNKNOWN_LINEAGE = "S_?"


def spider_class_to_lineage(spider: Spider) -> Lineage:
    """
    Provide an indication of the origin of the spider.
    :param spider: the spider
    :return: an indication of the origin the spider
    """
    return spider_path_to_lineage(sys.modules[spider.__module__].__file__)


def spider_path_to_lineage(file_path: str) -> Lineage:
    """
    Provide an indication of the origin of the spider.
    :param file_path: the location of the spider on the file system
    :return: an indication of the origin the spider
    """
    if "locations/spiders/government/" in file_path:
        return Lineage.S_ATP_GOV
    elif "locations/spiders/aggregator/" in file_path:
        return Lineage.S_ATP_AGG
    elif "locations/spiders/infrastructure" in file_path:
        return Lineage.S_ATP_INFRA
    elif "locations/spiders/addresses" in file_path:
        return Lineage.S_ATP_ADDRESSES
    elif "locations/spiders/" in file_path:
        return Lineage.S_ATP_BRANDS
    else:
        return Lineage.UNKNOWN_LINEAGE


class AddLineageExtension:

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls()
        crawler.signals.connect(ext.spider_opened, signal=spider_opened)
        return ext

    def spider_opened(self, spider: Spider):
        spider.crawler.stats.set_value("atp/lineage", spider_class_to_lineage(spider).value)
