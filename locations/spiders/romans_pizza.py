from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class RomansPizzaSpider(Spider):
    name = "romans_pizza"
    start_urls = ["https://romanspizza.co.za/api"]
    item_attributes = {"brand_wikidata": "Q65079427"}

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(
                url=url,
                method="POST",
                data={
                    "query": "{\n  stores {\n    id\n    lat\n    lng\n    uuid\n    halaal\n    name\n    address\n    area\n    phone\n    phoneTwo\n    phoneThree\n    phoneFour\n    isOnline\n    isAuraOnline\n    isTabletConnected\n    deliveryEnabled\n    hasDevice\n    hasGenerator\n    isKdsEnabled\n    externalId\n    day_0\n    day_1\n    day_2\n    day_3\n    day_4\n    day_5\n    day_6\n    isOnTheGo\n    paymentGateway\n    isTemporarilyClosed\n    deliveryFee\n  }\n}\n",
                },
            )

    def parse(self, response):
        for location in response.json()["data"]["stores"]:
            if location["isTemporarilyClosed"]:
                continue
            location["id"] = location.pop("uuid")
            phones = [
                location.get("phone"),
                location.get("phoneTwo"),
                location.get("phoneThree"),
                location.get("phoneFour"),
            ]
            location["phone"] = "; ".join([p for p in phones if p != "0"])

            item = DictParser.parse(location)

            item["branch"] = item.pop("name")
            apply_yes_no(Extras.BACKUP_GENERATOR, item, location["hasGenerator"], False)
            apply_yes_no(Extras.HALAL, item, location["halaal"], False)
            apply_yes_no(Extras.DELIVERY, item, location["deliveryEnabled"], False)

            oh = OpeningHours()
            for i in range(7):
                oh.add_ranges_from_string(location["day_" + str(i)])
            item["opening_hours"] = oh.as_opening_hours()

            yield item
