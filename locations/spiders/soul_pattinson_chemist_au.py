from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class SoulPattinsonChemistAUSpider(SuperStoreFinderSpider):
    name = "soul_pattinson_chemist_au"
    item_attributes = {"brand": "Soul Pattinson Chemist", "brand_wikidata": "Q117225301"}
    allowed_domains = ["soulpattinson.com.au"]
