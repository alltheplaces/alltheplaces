from typing import Iterable

from chompjs import chompjs
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.react_server_components import parse_rsc


class HobbyLobbyUSSpider(SitemapSpider, JSONBlobSpider):
    name = "hobby_lobby_us"
    allowed_domains = ["www.hobbylobby.com"]
    item_attributes = {
        "brand": "Hobby Lobby",
        "brand_wikidata": "Q5874938",
    }
    sitemap_urls = ["https://www.hobbylobby.com/sitemap-Store.xml"]
    sitemap_rules = [
        (r"/stores/search/(\d+)$", "parse"),
    ]

    def extract_json(self, response: TextResponse) -> list[dict]:
        objs = [
            chompjs.parse_js_object(s)
            for s in response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        ]
        rsc = "".join([s for n, s in objs]).encode()
        return [DictParser.get_nested_key(dict(parse_rsc(rsc)), "storeDetails")["data"]]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = feature["commonName"].split("-")[0].strip()
        item["website"] = response.url
        item["opening_hours"] = self.parse_opening_hours(feature.get("thisWeek", {}).get("hours", []))
        apply_category(Categories.SHOP_CRAFT, item)
        yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        opening_hours = OpeningHours()
        for rule in rules:
            if rule["startTime"].lower() == "closed":
                opening_hours.set_closed(rule["day"])
                continue
            opening_hours.add_range(rule["day"], rule["startTime"], rule["endTime"], "%I:%M %p")
        return opening_hours
