from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class ChickenTreatAUSpider(Spider):
    name = "chicken_treat_au"
    item_attributes = {"brand": "Chicken Treat", "brand_wikidata": "Q5096274"}
    allowed_domains = ["www.chickentreat.com.au"]
    start_urls = [
        "https://www.chickentreat.com.au/api-proxy/stores?include=amenities,availability,delivery,collection,holiday,storeAddress,salesforce"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}  # HTML error page returned for robots.txt

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["data"]:
            if not location["attributes"]["isEnabled"]:
                continue
            item = DictParser.parse(location["attributes"])
            item["ref"] = location["attributes"]["storeNumber"]
            address_fields = location["relationships"]["storeAddress"]["data"]["attributes"]["addressComponents"]
            item["street_address"] = address_fields["streetName"]["value"]
            item["extras"] = {}
            if address_fields["unit"]["value"]:
                item["extras"]["addr:unit"] = address_fields["unit"]["value"]
            if address_fields["floor"]["value"]:
                item["extras"]["addr:floor"] = address_fields["floor"]["value"]
            item["housenumber"] = address_fields["streetNumber"]["value"]
            item["city"] = address_fields["suburb"]["value"]
            item["state"] = address_fields["state"]["value"]
            item["postcode"] = address_fields["postcode"]["value"]
            item["website"] = "https://www.chickentreat.com.au/locations/" + location["attributes"][
                "storeName"
            ].lower().replace(" ", "-")
            item["opening_hours"] = OpeningHours()
            for day_hours in location["relationships"]["collection"]["data"]["attributes"]["collectionTimes"]:
                for time_period in day_hours["collectionTimePeriods"]:
                    item["opening_hours"].add_range(
                        day_hours["dayOfWeek"], time_period["openTime"], time_period["closeTime"], "%H:%M:%S"
                    )
            apply_yes_no(
                Extras.TOILETS, item, location["relationships"]["amenities"]["data"]["attributes"]["haveToilet"], False
            )
            apply_yes_no(
                Extras.WIFI, item, location["relationships"]["amenities"]["data"]["attributes"]["haveWifi"], False
            )
            apply_yes_no(Extras.DELIVERY, item, location["attributes"]["isDeliveryEnabled"], False)
            apply_yes_no(Extras.TAKEAWAY, item, location["attributes"]["isCollectionEnabled"], False)
            apply_yes_no(Extras.DRIVE_THROUGH, item, location["attributes"]["pickupTypes"]["driveThru"], False)
            yield item
