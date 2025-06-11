import json

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class SephoraUSCASpider(SitemapSpider, StructuredDataSpider):
    name = "sephora_us_ca"
    item_attributes = {"brand": "Sephora", "brand_wikidata": "Q2408041"}
    sitemap_urls = [
        "https://www.sephora.com/sephora-store-sitemap.xml",
        "https://www.sephora.com/sephora-store-sitemap_en-CA.xml",
    ]
    sitemap_rules = [
        (r"\/happening\/stores\/(?!kohls).+", "parse_sd"),
        (r"\/ca\/en\/happening\/stores\/(?!kohls).+", "parse_sd"),
    ]
    user_agent = BROWSER_DEFAULT

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item.pop("image")
        apply_category(Categories.SHOP_COSMETICS, item)
        if "sephora.com" in response.url:
            item["country"] = json.loads(response.xpath('//*[@id="linkStore"]/text()').get())["ssrProps"][
                "ErrorBoundary(ReduxProvider(StoreDetail))"
            ]["stores"][0]["address"]["country"]
        yield item
