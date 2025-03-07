import sys
from enum import Enum
from typing import Type

from scrapy import Spider
from scrapy.signals import spider_opened


class Lineage(Enum):
    Aggregators = "S_ATP_AGGREGATORS"
    Brands = "S_ATP_BRANDS"
    Governments = "S_ATP_GOVERNMENTS"
    Infrastructure = "S_ATP_INFRASTRUCTURE"
    Addresses = "S_ATP_ADDRESSES"
    Unknown = "S_?"


def spider_class_to_lineage(spider: Type) -> Lineage:
    """
    Provide an indication of the origin of the spider.
    :param spider: the spider
    :return: an indication of the origin the spider
    """

    if hasattr(spider, "lineage"):
        return getattr(spider, "lineage")

    file_path = sys.modules[spider.__module__].__file__

    if "locations/spiders/government/" in file_path:
        return Lineage.Governments
    elif "locations/spiders/aggregators/" in file_path:
        return Lineage.Aggregators
    elif "locations/spiders/infrastructure/" in file_path:
        return Lineage.Infrastructure
    elif "locations/spiders/addresses/" in file_path:
        return Lineage.Addresses
    elif "locations/spiders/" in file_path:
        return Lineage.Brands
    else:
        return Lineage.Unknown


class AddLineageExtension:

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls()
        crawler.signals.connect(ext.spider_opened, signal=spider_opened)
        return ext

    def spider_opened(self, spider: Spider):
        spider.crawler.stats.set_value("atp/lineage", spider_class_to_lineage(spider).value)
