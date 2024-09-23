import json
import re
from typing import Any

from parsel import Selector
from scrapy import Request
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule, Spider

from locations.linked_data_parser import LinkedDataParser


class BjRestaurantUSSpider(Spider):
    name = "bj_restaurant_us"
    item_attributes = {"brand": "BJ's Restaurant & Brewery", "brand_wikidata": "Q4835755"}
    start_urls = ["https://www.bjsrestaurants.com/sitemap"]
    rules = [Rule(LinkExtractor(r"https://www.bjsrestaurants.com/locations/\w\w/\w+"), "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        sel = Selector(
            text=json.loads(response.xpath('//script[@id="__NEXT_DATA__"][@type="application/json"]/text()').get())[
                "props"
            ]["pageProps"]["model"][":items"]["root"][":items"]["responsivegrid"][":items"]["text"]["text"]
        )
        link_format = re.compile(r"https://www.bjsrestaurants.com/locations/\w\w/\w+")
        for link in sel.xpath('//a[contains(@href, "/locations/")]/@href').getall():
            if link_format.match(link):
                yield Request(url=link, callback=self.parse_store)

    def parse_store(self, response: Response, **kwargs: Any) -> Any:
        f = json.loads(response.xpath('//script[@id="__NEXT_DATA__"][@type="application/json"]/text()').get())
        restaurant_data = f["props"]["pageProps"]["model"][":items"]["root"][":items"]["responsivegrid"][":items"][
            "restaurantdetails"
        ]["restaurant"]
        nested_json = json.loads(restaurant_data["seoScript"])
        item = LinkedDataParser.parse_ld(nested_json, time_format="%H:%M:%S")
        item["ref"] = restaurant_data["restaurantId"]
        item["branch"] = item.pop("name", None)
        item["website"] = response.urljoin(item["website"])
        yield item
