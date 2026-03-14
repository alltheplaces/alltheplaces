from locations.storefinders.nomnom import NomNomSpider


class WingstopGBSpider(NomNomSpider):
    name = "wingstop_gb"
    item_attributes = {"brand": "Wingstop", "brand_wikidata": "Q8025339"}
    start_urls = ["https://www.wingstop.co.uk/api/stores"]
