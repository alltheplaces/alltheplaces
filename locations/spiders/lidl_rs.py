from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlRSSpider(VirtualEarthSpider):
    name = "lidl_rs"
    item_attributes = {"brand": "Lidl", "brand_wikidata": "Q114509929"}
    dataset_id = "b903122d47ce4e8497d880eacd909971"
    dataset_name = "Filialdaten-RS/Filialdaten-RS"
    api_key = "AiCR22CCnnBs-mBEAKhUEpGOsjLeGPpSpOPvxi9KHpVZRjUkBJz8TYbTgwYBpstC"
