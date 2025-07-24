from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature


class ChickenTreatAUSpider(Spider):
    name = "chicken_treat_au"
    item_attributes = {"brand": "Chicken Treat", "brand_wikidata": "Q5096274"}
    allowed_domains = ["d3c377j0gjsips.cloudfront.net"]
    start_urls = ["https://d3c377j0gjsips.cloudfront.net/ct_all_store_sync.json"]

    def parse(self, response: Response) -> Iterable[Feature]:
        for location in response.json()["data"]:
            if not location["attributes"]["isEnabledForTrading"]:
                continue
            if not location["attributes"]["isCollectionEnabled"] and not location["attributes"]["isDeliveryEnabled"]:
                continue
            item = Feature()
            item["ref"] = location["id"]
            item["branch"] = location["attributes"]["storeName"]
            item["email"] = location["attributes"]["storeEmail"]
            item["phone"] = location["attributes"]["storePhone"]
            address_fields = location["relationships"]["storeAddress"]["data"]["attributes"]["addressComponents"]
            item["lat"] = address_fields["latitude"]["value"]
            item["lon"] = address_fields["longitude"]["value"]
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
            item["website"] = (
                "https://www.chickentreat.com.au/locations/"
                + location["relationships"]["slug"]["data"]["attributes"]["slug"]
            )
            item["opening_hours"] = OpeningHours()
            for day_hours in location["relationships"]["collection"]["data"]["attributes"]["collectionTimes"]:
                for time_period in day_hours["collectionTimePeriods"]:
                    item["opening_hours"].add_range(
                        day_hours["dayOfWeek"], time_period["openTime"], time_period["closeTime"], "%H:%M:%S"
                    )
            apply_category(Categories.FAST_FOOD, item)
            apply_yes_no(
                Extras.TOILETS, item, location["relationships"]["amenities"]["data"]["attributes"]["haveToilet"], False
            )
            apply_yes_no(
                Extras.WIFI, item, location["relationships"]["amenities"]["data"]["attributes"]["haveWifi"], False
            )
            apply_yes_no(Extras.DELIVERY, item, location["attributes"]["isDeliveryEnabled"], False)
            apply_yes_no(Extras.TAKEAWAY, item, location["attributes"]["isCollectionEnabled"], False)
            yield item
