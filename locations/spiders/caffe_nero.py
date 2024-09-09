import re
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class CaffeNeroSpider(Spider):
    name = "caffe_nero"
    item_attributes = {"brand": "Caffè Nero", "brand_wikidata": "Q675808"}
    allowed_domains = ["caffenero.com", "greencaffenero.pl", "caffenerowebsite.blob.core.windows.net"]
    start_urls = [
        "https://www.caffenero.com/cy/stores",
        "https://www.caffenero.com/ie/stores",
        "https://www.greencaffenero.pl/pl/stores",
        "https://www.caffenero.com/se/stores",
        "https://www.caffenero.com/tr/stores",
        "https://www.caffenero.com/ae/stores",
        "https://www.caffenero.com/uk/stores",
        "https://www.caffenero.com/us/stores",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield JsonRequest(
            re.search(r"loadGeoJson\(\n\s+'(https://.+)', {", response.text).group(1),
            callback=self.parse_geojson,
            meta={"root": response.url},
        )

    def parse_geojson(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["features"]:
            if (
                not location["properties"]["status"]["open"]
                or location["properties"]["status"]["opening_soon"]
                or location["properties"]["status"]["temp_closed"]
            ):
                continue

            item = DictParser.parse(location["properties"])
            item["geometry"] = location["geometry"]
            item["branch"] = item.pop("name")
            item["website"] = "{}/{}/".format(response.meta["root"], location["properties"]["slug"])

            if location["properties"]["status"]["express"]:
                item["name"] = "Nero Express"
            elif "stores-pl.json" in response.url:
                item["name"] = "Green Caffè Nero"
            else:
                item["name"] = "Caffè Nero"

            item["opening_hours"] = OpeningHours()
            for day_name, day_hours in location["properties"]["hoursRegular"].items():
                if day_hours["open"] == "closed" or day_hours["close"] == "closed":
                    item["opening_hours"].set_closed(day_name)
                if day_name == "holiday":
                    continue
                item["opening_hours"].add_range(day_name, day_hours["open"], day_hours["close"])

            apply_yes_no(Extras.TAKEAWAY, item, location["properties"]["status"]["takeaway"], False)
            apply_yes_no(Extras.DELIVERY, item, location["properties"]["status"]["delivery"], False)
            apply_yes_no(Extras.WIFI, item, location["properties"]["amenities"]["wifi"], False)
            apply_yes_no(Extras.TOILETS, item, location["properties"]["amenities"]["toilet"], False)
            apply_yes_no(Extras.BABY_CHANGING_TABLE, item, location["properties"]["amenities"]["baby_change"], False)
            apply_yes_no(Extras.SMOKING_AREA, item, location["properties"]["amenities"]["smoking_area"], False)
            apply_yes_no(Extras.AIR_CONDITIONING, item, location["properties"]["amenities"]["air_conditioned"], False)
            apply_yes_no(Extras.WHEELCHAIR, item, location["properties"]["amenities"].get("disabled_access"), False)
            apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, location["properties"]["amenities"]["disabled_toilet"], False)
            apply_yes_no(Extras.OUTDOOR_SEATING, item, location["properties"]["amenities"]["outside_seating"], False)

            apply_category(Categories.COFFEE_SHOP, item)

            yield item
