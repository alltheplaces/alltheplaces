from locations.storefinders.storemapper import StoremapperSpider


class GoldenDiscsIESpider(StoremapperSpider):
    name = "golden_discs_ie"
    item_attributes = {"brand": "Golden Discs", "brand_wikidata": "Q5579324"}
    key = "4298"
