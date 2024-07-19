from locations.storefinders.woosmap import WoosmapSpider


class RsgGroupSpider(WoosmapSpider):
    name = "rsg_group"
    key = "woos-3cb8caa3-ad4d-3e7b-b7d6-221a7b72398d&stores_by_page=300"
    origin = "https://www.mcfit.com"

    JOHN_REED = {"brand": "JOHN REED Fitness", "brand_wikidata": "Q106434148"}
    MC_FIT = {"brand": "McFit", "brand_wikidata": "Q871302"}
    HIGH_5 = {"brand": "High5", "brand_wikidata": "Q116183459"}

    BRANDS = {
        "JR": JOHN_REED,
        "JOHN REED Fitness": JOHN_REED,
        "McFIT": MC_FIT,
        "Palestra McFIT": MC_FIT,
        "H5": HIGH_5,
    }

    def parse_item(self, item, feature, **kwargs):
        if feature["properties"]["user_properties"].get("closed", False):
            return
        if item["ref"] == "5814289014024709637":
            return  # Head Office
        if "COMING SOON" in item["name"].upper():
            return

        brand_id = feature["properties"]["types"][0]
        if brand_id in ["GG", "franchise"]:
            return  # GoldsGymSpider

        if brand := self.BRANDS.get(brand_id):
            item.update(brand)
        else:
            item.update(self.MC_FIT)
        yield item
