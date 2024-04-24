import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.geo import point_locations, vincenty_distance


class SaveALotUSSpider(Spider):
    name = "save_a_lot_us"
    item_attributes = {"brand": "Save-A-Lot", "brand_wikidata": "Q7427972", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["savealot.com"]

    def start_requests(self):
        for lat, lon in point_locations("us_centroids_iseadgg_48km_radius.csv"):
            # Create a bounding box that fully encloses a circle of the given
            # search radius.
            circle_north = vincenty_distance(lat, lon, 50, 0)
            circle_east = vincenty_distance(lat, lon, 50, 90)
            circle_south = vincenty_distance(lat, lon, 50, 180)
            circle_west = vincenty_distance(lat, lon, 50, 270)
            box_sw = (circle_south[0], circle_west[1])
            box_ne = (circle_north[0], circle_east[1])
            yield JsonRequest(
                url=f"https://savealot.com/wp-json/locator/v1/search/{lat}/{lon}/{box_sw[0]}/{box_sw[1]}/{box_ne[0]}/{box_ne[1]}/"
            )

    def parse(self, response):
        locations = response.json()
        if len(locations) == 50:
            raise RuntimeError(
                "Locations have probably been truncated due to 50 (or more) locations being returned by a single geographic radius search. Use a more granular searchable points file."
            )
        for location in locations:
            item = DictParser.parse(location)
            item["ref"] = location["store"]

            city_uri_safe = re.sub(r"[^\w\-]", "", item["city"].lower().replace(" ", "-"))
            postcode = item["postcode"]
            store_number = item["ref"]
            item["website"] = f"https://savealot.com/grocery-stores/{city_uri_safe}-{postcode}-{store_number}/"

            yield item
