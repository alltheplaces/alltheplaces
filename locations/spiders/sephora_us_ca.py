import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
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

    def post_process_item(self, item, response, ld_data):
        item.pop("image")
        hours_string = " ".join(ld_data["openingHours"])
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        apply_category(Categories.SHOP_COSMETICS, item)
        if "sephora.com" in response.url:
            item["country"] = json.loads(response.xpath('//*[@id="linkStore"]/text()').get())["ssrProps"][
                "ErrorBoundary(ReduxProvider(StoreDetail))"
            ]["stores"][0]["address"]["country"]
        yield item
