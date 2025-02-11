import base64
import json

from scrapy import Request, Spider
from scrapy.selector import Selector

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class KekeSpider(Spider):
    name = "keke"
    item_attributes = {"brand": "Keke's Breakfast Cafe", "brand_wikidata": "Q115930150"}
    start_urls = ["https://www.kekes.com/_api/v1/access-tokens"]

    def parse(self, response):
        query = {
            "dataCollectionId": "Locations",
            "query": {"paging": {"limit": 1000}},
            "environment": "LIVE",
            "appId": "8c1ec64c-b621-4d3a-9cad-af08be8eba54",
        }
        encoded_query = base64.b64encode(json.dumps(query).encode()).decode()
        sv_session = response.json()["svSession"]
        yield Request(
            f"https://www.kekes.com/_api/cloud-data/v2/items/query?.r={encoded_query}",
            headers={"Cookie": f"svSession={sv_session}"},
            callback=self.parse_query_response,
        )

    def parse_query_response(self, response):
        for data_item in response.json()["dataItems"]:
            location = data_item["data"]
            if location["comingSoonYN"]:
                continue

            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["ref"] = location["_id"]
            item["addr_full"] = location["address"].get("formatted")
            item["street_address"] = location["address"]["streetAddress"].get("formattedAddressLine")
            item["extras"]["addr:unit"] = location["address"]["streetAddress"].get("apt")
            item["street"] = location["address"]["streetAddress"].get("name")
            item["housenumber"] = location["address"]["streetAddress"].get("number")
            item["state"] = location["address"].get("subdivision")
            item["lat"] = location["markerLat"]
            item["lon"] = location["markerLng"]
            item["extras"]["website:orders"] = location.get("ezChowUrl")
            item["website"] = response.urljoin(location["link-locations-1-title"])
            item["phone"] = Selector(text=location["phoneNumber"]).xpath("//text()").get()

            apply_yes_no("drink:alcohol", item, location.get("alcoholYN", False))
            apply_yes_no(Extras.DELIVERY, item, location.get("deliveryYN", False))
            apply_yes_no(Extras.INDOOR_SEATING, item, location.get("dineInYN", False))
            apply_yes_no(Extras.OUTDOOR_SEATING, item, location.get("outdoorSeatingYN", False))
            apply_yes_no(Extras.TAKEAWAY, item, location.get("pickupYN", False))

            oh = OpeningHours()
            oh.add_ranges_from_string(f"Daily {location['hours']}")
            item["opening_hours"] = oh

            if location.get("cateringYN"):
                apply_category(Categories.CRAFT_CATERER, item)
            apply_category(Categories.RESTAURANT, item)

            yield item
