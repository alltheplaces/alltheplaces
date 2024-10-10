from locations.storefinders.amai_promap import AmaiPromapSpider


class WaterdropSpider(AmaiPromapSpider):
    name = "waterdrop"
    item_attributes = {"brand": "Waterdrop", "brand_wikidata": "Q104178991"}
    start_urls = ["https://www.waterdrop.fr/pages/stores"]
