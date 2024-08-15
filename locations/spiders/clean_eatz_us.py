from locations.storefinders.rio_seo import RioSeoSpider


class CleanEatzUSSpider(RioSeoSpider):
    name = "clean_eatz_us"
    item_attributes = {
        "brand_wikidata": "Q124412638",
        "brand": "Clean Eatz",
    }
    domain = "locations.cleaneatz.com"
