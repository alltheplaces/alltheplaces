from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class JetsPizzaSpider(SitemapSpider, StructuredDataSpider):
    name = "jets_pizza"
    item_attributes = {"brand": "Jet's Pizza", "brand_wikidata": "Q16997713"}
    allowed_domains = ["www.jetspizza.com"]
    sitemap_urls = ["https://www.jetspizza.com/jp_store-sitemap.xml"]
    sitemap_rules = [(r"^https://www\.jetspizza\.com/stores/[^/]+/[^/]+/[^/]+/$", "parse_sd")]
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        del item[
            "name"
        ]  # generic "Jet's Pizza <address> (<store code>)" on every page, backfilled from item_attributes
        if ld_data.get("identifier"):
            item["ref"] = ld_data["identifier"]
        item["extras"]["website:orders"] = response.xpath('//a[contains(@href, "order.jetspizza.com")]/@href').get()

        apply_category(Categories.RESTAURANT, item)

        yield item
