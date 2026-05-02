import sys
from enum import Enum
from typing import Self

from scrapy import Spider
from scrapy.crawler import Crawler
from scrapy.signals import spider_opened


class Lineage(Enum):
    Addresses = "S_ATP_ADDRESSES"
    Aggregators = "S_ATP_AGGREGATORS"
    Brands = "S_ATP_BRANDS"
    Governments = "S_ATP_GOVERNMENTS"
    Infrastructure = "S_ATP_INFRASTRUCTURE"
    Unknown = "S_?"

    @property
    def group(self) -> str:
        return _LINEAGE_TO_GROUP.get(self, "brands")


_LINEAGE_TO_GROUP = {
    Lineage.Addresses: "addresses",
    Lineage.Aggregators: "aggregators",
    Lineage.Brands: "brands",
    Lineage.Governments: "government",
    Lineage.Infrastructure: "infrastructure",
    Lineage.Unknown: "brands",
}

_GROUP_TO_LINEAGE = {v: k for k, v in _LINEAGE_TO_GROUP.items() if k != Lineage.Unknown}

VALID_GROUPS = set(_GROUP_TO_LINEAGE.keys())


def lineage_for_group(group: str) -> "Lineage":
    if group not in _GROUP_TO_LINEAGE:
        raise ValueError(f"Unknown group: {group!r}. Valid groups: {sorted(VALID_GROUPS)}")
    return _GROUP_TO_LINEAGE[group]


def spider_class_to_lineage(spider: Spider | type[Spider]) -> Lineage:
    """
    Provide an indication of the origin of the spider.
    :param spider: the spider
    :return: an indication of the origin the spider
    """

    if hasattr(spider, "lineage"):
        return getattr(spider, "lineage")

    file_path = sys.modules[spider.__module__].__file__
    if not file_path:
        return Lineage.Unknown

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
    def from_crawler(cls, crawler: Crawler) -> Self:
        ext = cls()
        crawler.signals.connect(ext.spider_opened, signal=spider_opened)
        return ext

    def spider_opened(self, spider: Spider) -> None:
        if not spider.crawler.stats:
            return
        spider.crawler.stats.set_value("atp/lineage", spider_class_to_lineage(spider).value)
