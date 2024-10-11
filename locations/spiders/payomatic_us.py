import json

from scrapy import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class PayomaticUSSpider(Spider):
    name = "payomatic_us"
    start_urls = ["https://www.payomatic.com/store-locator/"]
    item_attributes = {
        "brand": "Payomatic",
        "brand_wikidata": "Q48742899",
        "extras": Categories.SHOP_MONEY_LENDER.value,
    }

    def parse(self, response):
        searchstr = "var stores_data = "
        script = response.xpath(f"//script[contains(text(), '{searchstr}')]/text()").get()
        start = script.find(searchstr) + len(searchstr)
        end = script.find(";\r\n", start)
        geojson = json.loads(script[start:end])
        for feature in geojson["features"]:
            item = DictParser.parse(feature["properties"])
            item["geometry"] = feature["geometry"]
            item["street_address"] = item.pop("addr_full")
            if item["phone"] in ("516-496-1970", "(516) 496-1970"):
                del item["phone"]

            oh = OpeningHours()
            for day, hours in feature["properties"]["store_hours"].items():
                if hours == "Closed":
                    oh.set_closed(day)
                elif hours == "24 Hours":
                    oh.add_range(day, "00:00", "23:59")
                else:
                    oh.add_ranges_from_string(f"{day} {hours}")
            item["opening_hours"] = oh

            yield item
