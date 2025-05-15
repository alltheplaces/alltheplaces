from locations.storefinders.nomnom import NomNomSpider


class WingstopSpider(NomNomSpider):
    name = "wingstop"
    item_attributes = {"brand": "Wingstop", "brand_wikidata": "Q8025339"}
    start_urls = ["https://api.wingstop.com/restaurants/"]
    use_calendar = False
