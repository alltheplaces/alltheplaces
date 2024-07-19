from locations.storefinders.uberall import UberallSpider


class GrandOpticalSpider(UberallSpider):
    name = "grand_optical"
    item_attributes = {"brand": "Grand Optical", "brand_wikidata": "Q3113677"}
    key = "3wg7zoSQ5DhaI1rhTTqlOG1fMUBRw0"
