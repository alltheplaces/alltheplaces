from locations.storefinders.storemapper import StoremapperSpider


class ObriensIESpider(StoremapperSpider):
    name = "obriens_ie"
    item_attributes = {"brand": "O'Briens", "brand_wikidata": "Q113151266"}
    key = "5830"
