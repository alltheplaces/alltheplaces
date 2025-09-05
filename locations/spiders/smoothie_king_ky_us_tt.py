from locations.items import Feature
from locations.storefinders.where2getit import Where2GetItSpider


class SmoothieKingKYUSTTSpider(Where2GetItSpider):
    name = "smoothie_king_ky_us_tt"
    item_attributes = {"brand": "Smoothie King", "brand_wikidata": "Q5491421"}
    api_endpoint = "https://locations.smoothieking.com/rest/getlist"
    api_key = "95B912AA-DEE4-11ED-883E-CDDDD7DDC1D0"
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 180}

    def parse_item(self, item: Feature, location: dict, **kwargs):
        item["name"] = None
        item["lat"], item["lon"] = location["latitude"], location["longitude"]
        yield item
