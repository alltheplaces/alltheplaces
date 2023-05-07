from locations.storefinders.storemapper import StoremapperSpider


class VPZGBSpider(StoremapperSpider):
    name = "vpz_gb"
    item_attributes = {"brand": "VPZ", "brand_wikidata": "Q107300487"}
    key = "14072"
