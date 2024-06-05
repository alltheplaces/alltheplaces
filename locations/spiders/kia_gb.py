from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.kia_au import KiaAUSpider


class KiaGBSpider(Spider):
    name = "kia_gb"
    item_attributes = KiaAUSpider.item_attributes
    allowed_domains = ["www.kia.com"]
    start_urls = [
        "https://www.kia.com/api/kia_uk/findByDealer.list?displayYn=Y&delYn=N&pagePerLines=99999999&locale=undefined-undefined&usedSellYn=N&servicingYn=Y"
    ]

    def parse(self, response):
        for location in response.json()["data"]["list"]:
            for location_type in ["sales", "service"]:
                if location_type == "service" and "servicingYn" == "N":
                    continue  # Servicing not available at this location

                item = DictParser.parse(location)
                item["ref"] = location.get("dealerNumber", str(location["dealerSeq"])) + f"_{location_type}"
                item["name"] = location["dealerName"]
                item["addr_full"] = clean_address(
                    [
                        location.get("address1"),
                        location.get("address2"),
                        location.get("address3"),
                        location.get("address4"),
                        location.get("address5"),
                        location.get("address6"),
                    ]
                )
                item["phone"] = location.get("salesPhone", location.get("aftersalesPhone"))
                if location["url"].startswith("kia.com"):
                    item["website"] = "https://www." + location["url"]
                elif location["url"].startswith("www.kia.com"):
                    item["website"] = "https://" + location["url"]

                hours_text = " ".join(
                    [
                        "{}: {}".format(day_hours["name"], day_hours["hours"])
                        for day_hours in location.get(f"{location_type}Hours", [])
                    ]
                )
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(hours_text)

                item["extras"] = {}
                if location_type == "sales":
                    apply_category(Categories.SHOP_CAR, item)
                else:
                    apply_category(Categories.SHOP_CAR_REPAIR, item)

                yield item
