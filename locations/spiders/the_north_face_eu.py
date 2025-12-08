from locations.items import Feature
from locations.storefinders.where2getit import Where2GetItSpider


class TheNorthFaceEUSpider(Where2GetItSpider):
    name = "the_north_face_eu"
    item_attributes = {"brand": "The North Face", "brand_wikidata": "Q152784"}
    api_brand_name = "northfaceeu"
    api_key = "3A992F50-193E-11E5-91BC-C90E919C4603"
    api_filter = {
        "or": {"northface": {"eq": ""}, "retailstore": {"eq": ""}, "outletstore": {"eq": ""}},
        "and": {
            "or": {
                "youth": {"eq": ""},
                "apparel": {"eq": ""},
                "mountain_athletics": {"eq": ""},
                "footwear": {"eq": ""},
                "equipment": {"eq": ""},
                "summit": {"eq": ""},
                "mt": {"eq": ""},
            }
        },
    }

    def parse_item(self, item: Feature, location: dict, **kwargs):
        if location["icon"] != "RetailStore":
            yield item
