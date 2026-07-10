from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class KieserTrainingSpider(SitemapSpider, StructuredDataSpider):
    name = "kieser_training"
    item_attributes = {"brand": "Kieser Training", "brand_wikidata": "Q1112367"}
    sitemap_urls = [
        "https://www.kieser.com/de-en/tx_kieserstudio/sitemap.xml",
        "https://www.kieser.com/ch-en/tx_kieserstudio/sitemap.xml",
        "https://www.kieser.com/at-en/tx_kieserstudio/sitemap.xml",
        "https://www.kieser.com/lu-en/tx_kieserstudio/sitemap.xml",
    ]
    sitemap_rules = [("/studios/", "parse_sd")]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("Kieser ", "")
        yield item
