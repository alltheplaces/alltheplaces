from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_3_LETTERS, OpeningHours


class HuwsGrayGBSpider(Spider):
    name = "huws_gray_gb"
    item_attributes = {"brand": "Huws Gray", "brand_wikidata": "Q16965780"}
    start_urls = ["https://www.huwsgray.co.uk/branch/ajax/stores"]
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for ref, location in response.json()["response"].items():
            item = DictParser.parse(location)
            item["ref"] = ref
            item["street_address"] = item.pop("street")
            item["website"] = location["infoLink"]

            if item["name"].startswith("Huws Gray "):
                item["branch"] = item.pop("name").removeprefix("Huws Gray ")

            item["opening_hours"] = OpeningHours()
            for day in DAYS_3_LETTERS:
                time = (
                    location["opening_hours_{}".format(day.lower())]
                    .replace("-1:00", "-13:00")
                    .replace("-4:30", "-16:30")
                    .replace("-4:45", "-16:45")
                    .replace("-5:00", "-17:00")
                    .replace("-5:15", "-17:15")
                )
                if time == "Closed":
                    item["opening_hours"].set_closed(day)
                else:
                    item["opening_hours"].add_range(day, *time.split("-"))

            apply_category(Categories.SHOP_TRADE, item)

            yield item
