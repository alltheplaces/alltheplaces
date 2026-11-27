from scrapy.http import Request

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.json_blob_spider import JSONBlobSpider


class SuzukiMotorcyclesAUSpider(JSONBlobSpider):
    name = "suzuki_motorcycles_au"
    item_attributes = {"brand": "Suzuki", "brand_wikidata": "Q181642"}

    async def start(self):
        yield Request(
            "https://api.suzukimotorcycles.com.au/public/dealers/search?lat=-37.8130&lng=144.9611&range=1000000&limit=200",
            headers={"Referer": "https://suzukimotorcycles.com.au/"},
        )

    def extract_json(self, response):
        features = response.json()
        if len(features) >= 200:
            raise ValueError("Suzuki dealer search reached its result limit")
        return features

    def post_process_item(self, item, response, feature):
        item["street_address"] = item.pop("addr_full")
        apply_category(Categories.SHOP_MOTORCYCLE, item)
        if feature["services"] and "Service" in feature["services"].split(","):
            apply_yes_no(Extras.MOTORCYCLE_REPAIR, item, True)
        yield item
