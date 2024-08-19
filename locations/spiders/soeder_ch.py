from locations.storefinders.storemapper import StoremapperSpider


class SoederCHSpider(StoremapperSpider):
    name = "soeder_ch"
    item_attributes = {
        "brand_wikidata": "Q111722324",
        "brand": "Soeder",
    }
    company_id = "16023-r6PfOZv3OfbeGfgX"
