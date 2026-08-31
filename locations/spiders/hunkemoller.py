import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class HunkemollerSpider(SitemapSpider):
    name = "hunkemoller"
    item_attributes = {"brand": "Hunkemöller", "brand_wikidata": "Q2604175"}
    sitemap_urls = ["https://www.hunkemoller.be/nl/sitemap-stores.xml"]
    sitemap_rules = [(r"https://www.hunkemoller.be/nl/winkel/[^/]+/[^/]+\-(\d+)$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = json.loads(response.xpath('//script[@id="mobify-data"]/text()').get())
        for q in data["__PRELOADED_STATE__"]["__reactQuery"]["queries"]:
            if "\u002fstores" in q["queryKey"]:
                poi = q["state"]["data"]["data"][0]
                break

        item = DictParser.parse(poi)
        item["branch"] = item.pop("name")
        item["website"] = response.url

        item["opening_hours"] = OpeningHours()
        for day, rule in (poi.get("c_hoursObj") or {}).items():
            item["opening_hours"].add_range(DAYS[int(day) - 2], rule["open"], rule["close"])

        apply_category(Categories.SHOP_CLOTHES, item)

        yield item
