from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_NL, OpeningHours


class PraxisNLSpider(SitemapSpider):
    name = "praxis_nl"
    item_attributes = {"brand": "Praxis", "brand_wikidata": "Q2741995"}
    sitemap_urls = ["https://www.praxis.nl/store/sitemap.xml"]

    # Structured data is not present for all store URLs
    def parse(self, response: Response, **kwargs: Any) -> Any:
        try:
            poi = chompjs.parse_js_object(
                response.xpath('//script[contains(text(), "storeDetail")]/text()').re_first(
                    r"storeDetail\s?=\s?(.*?});"
                ),
                json_params={"strict": False},
            )
        except Exception:
            return
        if not poi["showStoreDetail"]:
            return
        poi.update(poi.pop("address"))
        poi["country"] = poi["country"].pop("isocode")
        poi["name"] = poi.pop("displayName")
        item = DictParser.parse(poi)
        item["branch"] = item.pop("name")
        item["addr_full"] = poi["formattedAddress"]
        item["website"] = response.url
        item["street_address"] = None

        item["opening_hours"] = OpeningHours()
        for day in poi["weekdays"]:
            if day["closed"]:
                item["opening_hours"].set_closed(DAYS_NL[day["weekDay"]])
            else:
                item["opening_hours"].add_range(
                    DAYS_NL[day["weekDay"]], day["openingTime"]["formattedHour"], day["closingTime"]["formattedHour"]
                )

        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
