from datetime import datetime, timedelta

from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_yes_no
from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address

AMENITIES_MAP = {"wifi": Extras.WIFI}


class StarbucksZASpider(JSONBlobSpider):
    name = "starbucks_za"
    item_attributes = {"brand": "Starbucks", "brand_wikidata": "Q37158", "extras": Categories.COFFEE_SHOP.value}
    locations_key = "stores"

    def start_requests(self):
        for lat, lon in country_iseadgg_centroids("ZA", 24):
            yield JsonRequest(url=f"https://www.starbucks.co.za/api/v1/store-finder?latLng={lat},{lon}")
        extra_locations = [
            (-34, 18.45),  # Cape Town
            (-33.8, 18.49),  # North Cape Town
            (-33.93, 18.87),  # Stellenbosch
            (-26.26, 28.12),  # Alberton
            (-26.17, 28.17),  # Bedfordview
        ]
        for lat, lon in extra_locations:
            yield JsonRequest(url=f"https://www.starbucks.co.za/api/v1/store-finder?latLng={lat},{lon}")

    def pre_process_data(self, location):
        location["address"] = clean_address(location["address"].split("\n"))

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        for amenity in location["amenities"]:
            if attribute := AMENITIES_MAP.get(amenity["type"]):
                apply_yes_no(attribute, item, True)
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/unhandled_amenity/{amenity['type']}")

        item["opening_hours"] = OpeningHours()
        today = datetime.today()
        for day_hours in location["hoursNext7Days"]:
            day = day_hours["name"]
            times = day_hours["description"]
            if day == "Today":
                day = DAYS[today.weekday()]
            elif day == "Tomorrow":
                day = DAYS[(today + timedelta(days=1)).weekday()]
            item["opening_hours"].add_ranges_from_string(day + " " + times)
        yield item
