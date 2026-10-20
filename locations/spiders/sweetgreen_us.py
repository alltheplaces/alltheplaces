from typing import Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SweetgreenUSSpider(CrawlSpider, StructuredDataSpider):
    name = "sweetgreen_us"
    item_attributes = {"brand": "Sweetgreen", "brand_wikidata": "Q18636413"}
    allowed_domains = ["www.sweetgreen.com"]
    start_urls = ["https://www.sweetgreen.com/locations/"]
    rules = [Rule(LinkExtractor(allow=r"/locations/([-\w]+)/?$"), callback="parse")]
    wanted_types = ["Restaurant"]
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if response.xpath('//h1[contains(@class, "page-location__header__title")]/span[contains(., "Coming soon")]'):
            return
        item["branch"] = item.pop("name").removeprefix("Sweetgreen - ")
        if item["branch"].endswith("Retired"):
            return
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        # Leading zeroes are stripped from postcodes by the source data.
        item["postcode"] = item["postcode"].zfill(5)
        apply_category(Categories.FAST_FOOD, item)
        yield item
