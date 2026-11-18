from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_3_LETTERS_FROM_SUNDAY, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class SuitsupplySpider(Spider):
    name = "suitsupply"
    item_attributes = {"brand": "Suitsupply", "brand_wikidata": "Q17149142"}
    start_urls = ["https://suitsupply.com/on/demandware.store/Sites-INT-Site/en_NL/Stores-FindStores"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "DEFAULT_REQUEST_HEADERS": {"X-Requested-With": "XMLHttpRequest"}}

    def parse(self, response: Response) -> Iterable[Request]:
        for country in response.json()["countryOptions"]:
            yield Request(f"{response.url}?country={country['id']}&showMap=false", callback=self.parse_locations)

    def parse_locations(self, response: Response) -> Iterable[Feature]:
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines([location["address1"], location["address2"]])
            item["website"] = f"https://suitsupply.com/en-nl/stores/{item['ref'].removeprefix('stores-')}"

            oh = OpeningHours()
            for data in location["storeHoursData"]:
                if data["open"] != "--:--":
                    oh.add_range(DAYS_3_LETTERS_FROM_SUNDAY[int(data["day"])], data["open"], data["close"])
            item["opening_hours"] = oh

            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
