from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AxaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "axa_fr"
    item_attributes = {"brand": "AXA", "brand_wikidata": "Q160054"}
    allowed_domains = ["agence.axa.fr"]
    sitemap_urls = ["https://agence.axa.fr/sitemap.xml"]
    sitemap_rules = [(r"/distributeur/(\d+)$", "parse_sd")]
    wanted_types = ["InsuranceAgency"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["ref"] = response.url.rsplit("/", 1)[-1]
        item["branch"] = item.pop("name", None)
        apply_category(Categories.OFFICE_INSURANCE, item)
        yield item
