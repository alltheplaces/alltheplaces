from typing import Any, AsyncIterator, Iterable

from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class TotalWineAndMoreUSSpider(Spider):
    name = "total_wine_and_more_us"
    item_attributes = {"brand": "Total Wine", "brand_wikidata": "Q7828084"}
    allowed_domains = ["www.totalwine.com"]
    start_urls = ["https://www.totalwine.com/store-finder/browse"]
    zyte_meta = {"zyte_api": {"httpResponseBody": True, "httpResponseHeaders": True}}

    async def start(self) -> AsyncIterator[Request]:
        for url in self.start_urls:
            yield Request(url, meta=self.zyte_meta)

    @staticmethod
    def extract_search(response: Response) -> dict:
        script = response.xpath('//script[contains(text(), "window.INITIAL_STATE")]/text()').get()
        return parse_js_object(script.split("window.INITIAL_STATE = ", 1)[1])["search"]["stores"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        for state in self.extract_search(response)["metadata"]["states"]:
            yield Request(
                f"https://www.totalwine.com/store-finder/browse/{state['stateIsoCode']}",
                callback=self.parse_state,
                meta=self.zyte_meta,
            )

    def parse_state(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in self.extract_search(response)["stores"]:
            item = DictParser.parse(location)
            item["ref"] = location["storeNumber"]
            item["branch"] = item.pop("name")
            item["street_address"] = clean_address([location.get("address1"), location.get("address2")])
            item["website"] = "https://www.totalwine.com/store-info/" + item["ref"]

            apply_yes_no(Extras.WIFI, item, location["wifiAvailable"], False)

            if location["storeHours"]["hasHours"]:
                item["opening_hours"] = OpeningHours()
                for day_hours in location["storeHours"]["days"]:
                    if day_hours["closedStatus"]:
                        item["opening_hours"].set_closed(day_hours["dayOfWeek"].title())
                    else:
                        item["opening_hours"].add_range(
                            day_hours["dayOfWeek"].title(),
                            day_hours["openingTime"],
                            day_hours["closingTime"],
                            "%I:%M %p",
                        )

            apply_category(Categories.SHOP_ALCOHOL, item)
            yield item
