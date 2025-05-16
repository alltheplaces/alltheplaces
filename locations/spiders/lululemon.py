import json

from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class LululemonSpider(SitemapSpider):
    name = "lululemon"
    item_attributes = {"brand": "Lululemon", "brand_wikidata": "Q6702957"}
    sitemap_urls = ("https://shop.lululemon.com/sitemap.xml",)
    sitemap_rules = [
        (r"^https://shop.lululemon.com/stores/[^/]+/[^/]+/[^/]+$", "parse_store"),
    ]

    def parse_store(self, response):
        data = json.loads(response.xpath('//script[@type="application/json"]/text()').extract_first())
        if store_data := data["props"]["pageProps"].get("storeData"):
            if store_data.get("storeStatus") == "active":
                item = DictParser.parse(store_data)
                item["website"] = response.url
                item["branch"] = item.pop("name")
                if opening_hours := store_data.get("hours"):
                    item["opening_hours"] = OpeningHours()
                    for time_period in opening_hours:
                        start_time = time_period.get("openHour")
                        end_time = time_period.get("closeHour")
                        if start_time and end_time:
                            item["opening_hours"].add_range(
                                time_period.get("name"), start_time, end_time, time_format="%H:%M"
                            )
                yield item
