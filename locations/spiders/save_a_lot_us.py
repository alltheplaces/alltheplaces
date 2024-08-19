from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS, OpeningHours


class SaveALotUSSpider(Spider):
    name = "save_a_lot_us"
    item_attributes = {"brand": "Save-A-Lot", "brand_wikidata": "Q7427972", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["savealot.com"]
    download_delay = 0.2

    def start_requests(self):
        # API returns stores within 25 miles of a provided WGS84 coordinate.
        for lat, lon in country_iseadgg_centroids(["US"], 79):
            yield JsonRequest(url=f"https://savealot.com/?lat={lat}&lng={lon}&_data=root")

    def parse(self, response):
        locations = response.json()["storeList"]["_embedded"]["matches"]

        # A maximum of 50 locations are returned at once. The search radius is
        # set to avoid receiving 50 locations in a single response. If 50
        # locations were to be returned, it is a sign that some locations have
        # most likely been truncated.
        if len(locations) >= 50:
            raise RuntimeError(
                "Locations have probably been truncated due to 50 (or more) locations being returned by a single geographic radius search, and the API restricts responses to 50 results only. Use a smaller search radius."
            )

        if len(locations) > 0:
            self.crawler.stats.inc_value("atp/geo_search/hits")
        else:
            self.crawler.stats.inc_value("atp/geo_search/misses")
        self.crawler.stats.max_value("atp/geo_search/max_features_returned", len(locations))

        for location in locations:
            location = location["details"]
            item = DictParser.parse(location)
            item["ref"] = location["number"]
            item["branch"] = item.pop("name", None)
            item["website"] = "https://savealot.com/stores/" + location["number"]
            item["street_address"] = location["location"]["address1"]
            item["city"] = location["location"]["city"]
            item["state"] = location["location"]["state"]
            item["postcode"] = location["location"]["postalCode"]
            item["country"] = location["location"]["country"]

            for phone_number in location["phoneNumbers"]:
                if phone_number["description"] == "Main":
                    item["phone"] = phone_number["value"]
                    break

            item["opening_hours"] = OpeningHours()
            for day_hours in location["hours"]:
                item["opening_hours"].add_range(
                    DAYS[day_hours["day"]], day_hours["hours"]["open"], day_hours["hours"]["close"], "%H:%M:%S"
                )

            yield item
