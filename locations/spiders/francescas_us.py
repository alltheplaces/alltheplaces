from locations.storefinders.storemapper import StoremapperSpider


class FrancescasUSSpider(StoremapperSpider):
    name = "francescas_us"
    item_attributes = {"brand": "Francesca's", "brand_wikidata": "Q72982331"}
    company_id = "16784"
