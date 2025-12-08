from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class NeuhausSpider(Spider):
    name = "neuhaus"
    item_attributes = {"brand": "Neuhaus", "brand_wikidata": "Q1813801"}
    start_urls = [
        "https://www.neuhauschocolates.com/on/demandware.store/Sites-Neuhaus-Webshop-US-Site/en_US/Stores-FindStores?showMap=false&attributes=isFlagship"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        for location in response.json()["stores"]:
            location["street_address"] = merge_address_lines([location.pop("address1"), location.pop("address2")])
            item = DictParser.parse(location)
            item["website"] = f'https://www.neuhauschocolates.com/en_US/stores/detail?store={item["ref"]}'

            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                if rule := location.get(f"openingHours{day}"):
                    if rule.get("open") and rule["open"] != "closed":
                        item["opening_hours"].add_range(
                            day, rule["open"], rule["close"], "%I:%M %p" if "M" in rule["open"] else "%H:%M"
                        )

            yield item
