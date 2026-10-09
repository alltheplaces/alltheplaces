from typing import Any, Iterable

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.react_server_components import parse_rsc

VODAFONE_SHARED_ATTRIBUTES = {"brand": "Vodafone", "brand_wikidata": "Q122141"}


class VodafoneDESpider(SitemapSpider):
    name = "vodafone_de"
    item_attributes = VODAFONE_SHARED_ATTRIBUTES
    allowed_domains = ["shops.vodafone.de"]
    sitemap_urls = ["https://shops.vodafone.de/sitemap.xml"]
    sitemap_rules = [(r"/de/[^/]+/[^/]+/\d+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        rsc = "".join(s for _, s in objs).encode()
        data = dict(parse_rsc(rsc))
        if not (shop := DictParser.get_nested_key(data, "shop")):
            return
        shop = {k: v for k, v in shop.items() if v != "$undefined"}

        item = DictParser.parse(shop)
        item["ref"] = shop["rmsId"]
        item["street_address"] = item.pop("addr_full")
        item["city"] = shop.get("city", {}).get("cityName")
        item["lon"], item["lat"] = shop["location"]
        item["website"] = response.url

        item["opening_hours"] = OpeningHours()
        for day in shop.get("openingHours", []):
            if day.get("isClosed"):
                item["opening_hours"].set_closed(DAYS_EN[day["day"].capitalize()])
                continue
            for interval in day.get("intervals", []):
                item["opening_hours"].add_range(DAYS_EN[day["day"].capitalize()], interval["open"], interval["close"])

        apply_category(Categories.SHOP_MOBILE_PHONE, item)

        yield item
