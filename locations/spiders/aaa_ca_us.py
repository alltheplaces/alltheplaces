from urllib.parse import urlencode

from scrapy import Request, Spider

from locations.categories import Categories
from locations.geo import country_iseadgg_centroids
from locations.items import Feature


class AaaCAUSSpider(Spider):
    name = "aaa_ca_us"
    item_attributes = {
        "brand": "American Automobile Association",
        "brand_wikidata": "Q463436",
        "extras": Categories.SHOP_TRAVEL_AGENCY.value,
    }
    allowed_domains = ["tdr.aaa.com"]

    def start_requests(self):
        for lat, lon in country_iseadgg_centroids(["CA", "US"], 79):
            params = {
                "searchtype": "O",
                "radius": "100",
                "format": "json",
                "ident": "AAACOM",
                "destination": f"{lat},{lon}",
            }
            yield Request("https://tdr.aaa.com/tdrl/search.jsp?" + urlencode(params))

    def parse(self, response):
        locations = response.json()["aaa"]["services"].get("travelItems")
        if not locations:
            return
        locations = locations.get("travelItem", [])
        # If result is a singleton POI then it is not supplied as a list! Make consistent.
        if not isinstance(locations, list):
            locations = [locations]

        if len(locations) > 0:
            self.crawler.stats.inc_value("atp/geo_search/hits")
        else:
            self.crawler.stats.inc_value("atp/geo_search/misses")
        self.crawler.stats.max_value("atp/geo_search/max_features_returned", len(locations))

        for location in locations:
            properties = {
                "ref": location["id"],
                "name": location["itemName"],
                "street_address": location["addresses"]["address"]["addressLine"],
                "city": location["addresses"]["address"]["cityName"],
                "state": location["addresses"]["address"]["stateProv"]["code"],
                "postcode": location["addresses"]["address"]["postalCode"],
                "country": location["addresses"]["address"]["countryName"]["code"],
                "lat": location["position"]["latitude"],
                "lon": location["position"]["longitude"],
                "phone": location["phones"].get("phone", {}).get("content"),
            }
            item = Feature(**properties)
            yield item
