from locations.storefinders.elfsight import ElfsightSpider


class Good2GoStoresUSSpider(ElfsightSpider):
    name = "good_2_go_stores_us"
    item_attributes = {"brand": "Good 2 Go", "brand_wikidata": "Q109826132"}
    start_urls = ["https://good2gostores.com/locations/"]
    no_refs = True
