import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class BjRestaurantUSSpider(SitemapSpider):
    name = "bj_restaurant_us"
    item_attributes = {"brand": "BJ's", "brand_wikidata": "Q4835755"}
    sitemap_urls = ["https://www.bjsrestaurants.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/\w\w/[\w-]+$", "parse_store")]

    def parse_store(self, response: Response) -> Any:
        f = json.loads(response.xpath('//script[@id="__NEXT_DATA__"][@type="application/json"]/text()').get())
        if "restaurantdetails" not in f.get("props", {}).get("pageProps", {}).get("model", {}):
            return
        restaurant_data = f["props"]["pageProps"]["model"]["restaurantdetails"]["restaurant"]
        nested_json = json.loads(restaurant_data["seoScript"])
        item = LinkedDataParser.parse_ld(nested_json, time_format="%H:%M:%S")
        item["ref"] = restaurant_data["restaurantId"]
        item["branch"] = item.pop("name", None)
        item["website"] = response.urljoin(item["website"])
        yield item
