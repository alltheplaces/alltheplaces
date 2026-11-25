import json
import re

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class GelsonsSpider(scrapy.spiders.SitemapSpider):
    name = "gelsons"
    item_attributes = {
        "brand": "Gelson's",
        "brand_wikidata": "Q16993993",
        "country": "US",
    }

    sitemap_urls = ["https://www.gelsons.com/sitemap.xml"]
    sitemap_rules = [("/stores/", "parse_store")]

    def sitemap_filter(self, entries):
        for entry in entries:
            if "virtual" in entry["loc"]:
                continue
            yield entry

    def parse_store(self, response):
        content = json.loads(response.xpath('//script[@type="application/json"]/text()').get())["props"]["pageProps"]
        store_json = content["store"]

        item = DictParser.parse(store_json)
        item["branch"] = item.pop("name")
        item["street_address"] = item.pop("addr_full", None)
        item["phone"] = store_json["storePhone"]
        item["website"] = response.url
        if hours := content["pageComponents"][0]["headline"]:
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                "Mo-Su " + re.sub(r"(\d)([ap])\b", r"\1\2m", hours.split(",")[0].removeprefix("Hours:"))
            )

        yield item
