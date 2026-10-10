import math
from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.geo import city_locations, country_iseadgg_centroids
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class AaaCAUSSpider(JSONBlobSpider):
    name = "aaa_ca_us"
    item_attributes = {"brand": "American Automobile Association", "brand_wikidata": "Q463436"}
    allowed_domains = ["www.aaa.com"]

    # GeoNames admin1 codes, which the API's geocoder does not understand.
    CA_PROVINCES = {
        "01": "AB",
        "02": "BC",
        "03": "MB",
        "04": "NB",
        "05": "NL",
        "07": "NS",
        "08": "ON",
        "09": "PE",
        "10": "QC",
        "11": "SK",
        "12": "YT",
        "13": "NT",
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        # The API only geocodes place names, so snap each grid cell to its nearest city and widen the radius to match.
        cities = [*city_locations("US"), *city_locations("CA")]
        cell_radius_miles = 196
        for lat, lon in country_iseadgg_centroids(["CA", "US"], 315):
            cos_lat = math.cos(math.radians(lat))
            city = min(cities, key=lambda c: (c["latitude"] - lat) ** 2 + ((c["longitude"] - lon) * cos_lat) ** 2)
            offset_miles = 69 * math.hypot(city["latitude"] - lat, (city["longitude"] - lon) * cos_lat)
            if offset_miles > cell_radius_miles:
                # No city in this cell (Arctic or open ocean), and very large radii make the API return HTTP 500.
                continue
            yield JsonRequest(
                url="https://www.aaa.com/sharedservices/officedata.jsp?type=addresssearch",
                data={
                    "meta": {"appid": "BOL", "club": "999"},
                    "types": {"office": {"clustered": False, "limit": 1000, "sort": [["distance", "asc"]]}},
                    "withinAddress": {
                        "city": city["name"],
                        "state": self.CA_PROVINCES.get(city["admin1code"], city["admin1code"]),
                        "radius": cell_radius_miles + offset_miles,
                    },
                },
            )

    def extract_json(self, response: TextResponse) -> list[dict]:
        return [
            office | office["addresses"][0]
            for category in response.json()["categories"]
            for office in category["items"]
        ]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["street_address"] = merge_address_lines([item["street_address"], feature["addressLine2"]])
        item["city"] = feature["city"]["text"]
        item["state"] = feature["stateProv"]["text"]
        item["phone"] = feature["phones"][0]["text"] if feature["phones"] else None

        item["opening_hours"] = OpeningHours()
        for day in feature["hours"][0]["days"]:
            if day.get("closed"):
                item["opening_hours"].set_closed(day["day"])
            for shift in day.get("shifts", []):
                item["opening_hours"].add_range(day["day"], shift["open"], shift["close"])

        apply_category(Categories.SHOP_TRAVEL_AGENCY, item)

        yield item
