import scrapy

from locations.categories import Categories, apply_category, apply_yes_no
from locations.items import Feature


class BestInParkingSpider(scrapy.Spider):
    name = "best_in_parking"
    item_attributes = {"operator": "Best in Parking", "operator_wikidata": "Q112118218"}
    allowed_domains = ["www.bestinparking.com"]
    start_urls = ["https://www.bestinparking.com/en/api/garages?f[0]=type:parking"]

    def parse(self, response):
        for poi in response.json()["search_results"]:
            item = Feature()
            item["ref"] = poi["nid"]
            item["name"] = poi["title"]
            item["country"] = poi["country"]
            item["website"] = poi["link"]
            item["street_address"] = poi["address_street"]
            item["postcode"] = poi["address_postcode"]
            item["image"] = poi.get("image", {}).get("media_image")
            item["extras"]["capacity"] = poi["parking_car_spaces"]
            apply_yes_no("fee", item, poi.get("cheapest_short_parking_tariff_price"))

            geo = poi.get("geolocation", "").split(", ")
            if geo:
                item["lat"] = geo[0]
                item["lon"] = geo[1]

            apply_category(Categories.PARKING, item)
            # TODO: map driveway_height attribute
            # TODO: figure out how to fetch opening_hours

            # There is also a status endpoint for each POI,
            # e.g. https://www.bestinparking.com/en/api/garages/live/2675
            yield item
