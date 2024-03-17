from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.storefinders.sylinder import SylinderSpider


class StorcashNoSpider(SylinderSpider):
    name = "storcash_no"
    item_attributes = {"brand": "Storcash", "extras": Categories.SHOP_WHOLESALE.value}
    base_url = "https://storcash.no/#"  # Note: Doesn't use the same storefinder
    app_keys = [
        "5000",  # Bergen Storcash Storcash (NO)
        "5020",  # Sola Storcash
        "5030",  # Haugaland Storcash
        "5040",  # Kjørbekk Storcash
        "5060",  # Tiller Storcash
        "5070",  # Sørlandet Storcash
        "5080",  # Buskerud Storcash
        "5090",  # Bodø Storcash
    ]

    def start_requests(self):
        yield JsonRequest(url="https://api.ngdata.no/sylinder/stores/v1/extended-info")

    def parse(self, response, **kwargs):
        for location in response.json():
            if not location["storeDetails"]["chainId"] in self.app_keys:
                continue

            yield from self.parse_location(location) or []
