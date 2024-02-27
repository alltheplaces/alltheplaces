from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.items import Feature


class CountryFireAuthority(Spider):
    name = "country_fire_authority_au"
    item_attributes = {
        "operator": "Country Fire Authority",
        "operator_wikidata": "Q13632973",
        "extras": Categories.FIRE_STATION.value,
    }
    allowed_domains = ["services-ap1.arcgis.com"]
    start_urls = [
        "https://services-ap1.arcgis.com/vh59f3ZyAEAhnejO/arcgis/rest/services/CFA_Fire_Stations/FeatureServer/0/query?where=1%3D1&outFields=site_id%2Cfs_name%2Clabel%2Cstreet%2Csuburb%2Cpcode%2Cadd_src%2Cfs_type%2Cpersonnel%2Cfs_st_date%2Cimage&returnGeometry=true&f=pgeojson"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["features"]:
            properties = {
                "ref": location["properties"]["site_id"],
                "name": location["properties"]["fs_name"],
                "street_address": location["properties"]["street"],
                "city": location["properties"]["suburb"],
                "postcode": location["properties"]["pcode"],
                "geometry": location["geometry"],
            }
            yield Feature(**properties)
