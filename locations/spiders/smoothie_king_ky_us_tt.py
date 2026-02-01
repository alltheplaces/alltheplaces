from locations.items import Feature
from locations.storefinders.where2getit import Where2GetItSpider


class SmoothieKingKYUSTTSpider(Where2GetItSpider):
    name = "smoothie_king_ky_us_tt"
    item_attributes = {"brand": "Smoothie King", "brand_wikidata": "Q5491421"}
    api_brand_name = "smoothiekingsites"
    api_key = "AA777E40-E5F4-11ED-B583-3193A96E38C4"
    custom_settings = {
        "DOWNLOAD_TIMEOUT": 30,
        "DOWNLOAD_WARNSIZE": 268435456,  # 256 MiB needed as results are >150 MiB
    }

    def parse_item(self, item: Feature, location: dict, **kwargs):
        item["name"] = None
        item["lat"], item["lon"] = location["latitude"], location["longitude"]
        yield item
