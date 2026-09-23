from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class GreencrossAUSpider(SitemapSpider, StructuredDataSpider):
    name = "greencross_au"
    allowed_domains = ["www.petbarn.com.au"]
    sitemap_urls = ["https://www.petbarn.com.au/media/sitemap/au/sitemap.xml"]
    sitemap_rules = [("/stores/", "parse_sd")]
    wanted_types = ["PetStore"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if "Greencross Vets" in item["name"]:
            item["brand"] = "Greencross Vets"
            item["brand_wikidata"] = "Q41179992"
            item["branch"] = item.pop("name").removeprefix("Greencross Vets ")
        else:
            item["brand"] = "Petbarn"
            item["brand_wikidata"] = "Q104746468"
            item["branch"] = item.pop("name").removeprefix("Petbarn ").removeprefix("Animal Emergency Centre ")
        yield item
