from locations.categories import apply_category
from locations.items import Feature
from locations.storefinders.where2getit import Where2GetItSpider


class YoshinoyaUSSpider(Where2GetItSpider):
    name = "yoshinoya_us"
    item_attributes = {"brand": "Yoshinoya","brand_wikidata": "Q776272"}
    api_endpoint = "https://locations.yoshinoyaamerica.com/rest/getlist"
    api_key = "5F63337C-CAA5-11EE-A3D6-FED4D2F445A6"

    def parse_item(self, item: Feature, location: dict, **kwargs):
        apply_category({"amenity": "restaurant", "cuisine": "japanese"}, item)
        yield item
