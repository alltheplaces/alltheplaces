from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class ManchuWokCAUSSpider(SuperStoreFinderSpider):
    name = "manchu_wok_ca_us"
    item_attributes = {
        "brand_wikidata": "Q6747622",
        "brand": "Manchu Wok",
    }
    allowed_domains = [
        "manchuwok.com",
    ]
