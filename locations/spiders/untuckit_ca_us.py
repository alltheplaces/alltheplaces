from locations.storefinders.storemapper import StoremapperSpider


class UntuckitCAUSSpider(StoremapperSpider):
    name = "untuckit_ca_us"
    item_attributes = {
        "brand_wikidata": "Q28207006",
        "brand": "UNTUCKit",
    }
    key = "5048"
