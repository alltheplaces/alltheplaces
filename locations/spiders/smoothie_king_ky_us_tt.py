from locations.items import Feature
from locations.storefinders.where2getit import Where2GetItSpider


class SmoothieKingKYUSTTSpider(Where2GetItSpider):
    name = "smoothie_king_ky_us_tt"
    item_attributes = {
        "brand_wikidata": "Q5491421",
        "brand": "Smoothie King",
    }
    api_endpoint = "https://locations.smoothieking.com/rest/getlist"
    api_key = "95B912AA-DEE4-11ED-883E-CDDDD7DDC1D0"
    download_timeout = 180

    def parse_item(self, item: Feature, location: dict, **kwargs):
        item["lat"], item["lon"] = location["latitude"], location["longitude"]
        yield item
