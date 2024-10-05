from locations.storefinders.amai_promap import AmaiPromapSpider


class WaterdropDESpider(AmaiPromapSpider):
    name = "waterdrop_de"   
    item_attributes = {"brand": "Waterdrop", "brand_wikidata": "Q104178991"}
    start_urls = ["https://www.waterdrop.de/pages/stores"]
