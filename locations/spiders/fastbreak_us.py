from locations.storefinders.storerocket import StoreRocketSpider


class FastbreakUSSpider(StoreRocketSpider):
    name = "fastbreak_us"
    item_attributes = {"brand": "Fastbreak", "brand_wikidata": "Q116731804"}
    storerocket_id = "WwzpABj4dD"
    base_url = "https://www.myfastbreak.com/locations"
