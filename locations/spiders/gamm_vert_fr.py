from locations.storefinders.uberall import UberallSpider


class GammVertFRSpider(UberallSpider):
    name = "gamm_vert_fr"
    item_attributes = {"brand": "Gamm Vert", "brand_wikidata": "Q3095006"}
    drop_attributes = {"name"}
    key = "eUuVj5S6aN1AQQbd8V922kp8cb3pmn"
