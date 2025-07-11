import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BredFRSpider(SitemapSpider):
    name = "bred_fr"
    item_attributes = {"brand": "BRED", "brand_wikidata": "Q2877455"}
    sitemap_urls = ["https://www.bred.fr/sitemap.xml"]
    sitemap_rules = [("/les-agences/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = json.loads(response.xpath('//*[@type="application/json"]/text()').get())
        keys = list(raw_data.keys())
        branch_data = raw_data[keys[0]]["b"]["store"]
        item = DictParser.parse(branch_data)
        item["branch"] = item.pop("name").removeprefix("Agence ")
        item["street_address"] = item.pop("addr_full")
        item["phone"] = item["phone"]["text"]
        item["email"] = branch_data["contact"]["mail"]["text"]
        item["postcode"], item["city"] = item["postcode"].split(" ", 1)
        item["website"] = response.url
        apply_category(Categories.BANK, item)

        item["opening_hours"] = OpeningHours()
        for day, times in branch_data["openingHours"].items():
            if times["morning"].get("isClosed") is True and times["afternoon"].get("isClosed") is True:
                item["opening_hours"].set_closed(day)
            else:
                for time in times.values():
                    if time.get("isClosed") is not True:
                        item["opening_hours"].add_range(day, time["start"], time["end"])

        yield item
