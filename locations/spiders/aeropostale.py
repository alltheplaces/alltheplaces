from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AeropostaleSpider(SitemapSpider, StructuredDataSpider):
    name = "aeropostale"
    item_attributes = {"brand": "Aeropostale", "brand_wikidata": "Q794565"}
    sitemap_urls = ["https://stores.aeropostale.com/robots.txt"]
    sitemap_rules = [(r"^https://stores.aeropostale.com/[^/]+/[^/]+/[^/]+$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["image"] = item["name"] = None
        item["branch"] = (
            response.xpath('//h1[@class="Hero-title Hero-title--aeropostale"]/text()')
            .get()
            .removeprefix("Aeropostale ")
            .split(",", 1)[0]
        )
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
