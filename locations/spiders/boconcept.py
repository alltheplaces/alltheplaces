from scrapy import Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BoconceptSpider(Spider):
    name = "boconcept"
    item_attributes = {"brand": "BoConcept", "brand_wikidata": "Q11338915"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ["https://www.boconcept.com/api/store/search/?locale=en-us&mb=-90%2C-180%2C90%2C180"]

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("street")

            amenities = {amenity["id"] for amenity in location["amenities"]}
            apply_yes_no(Extras.DELIVERY, item, "deliveryassembly" in amenities)
            apply_yes_no(
                Extras.WHEELCHAIR,
                item,
                not amenities.isdisjoint({"wheelchairelevator", "wheelchairenterance", "wheelchairparking"}),
            )
            apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, "wheelchairrestroom" in amenities)

            oh = OpeningHours()
            for day in location["normalWeekOpeningHours"].values():
                if day["closed"]:
                    oh.set_closed(day["dayOfWeek"])
                else:
                    for row in day["openingHoursList"]:
                        oh.add_range(day["dayOfWeek"], row["open"], row["close"])
            item["opening_hours"] = oh

            contact_info = location["contactInformation"]
            item["email"] = contact_info["email"]
            if contact_info["phone"]:
                if contact_info["phone"].startswith("+"):
                    item["phone"] = contact_info["phone"]
                else:
                    item["phone"] = f"{contact_info['phoneCountryCode']} {contact_info['phone']}"

            if location["images"]:
                item["image"] = location["images"][0]["imageUrl"]
            if location["storePageUrl"]:
                item["website"] = response.urljoin(location["storePageUrl"])

            yield item
