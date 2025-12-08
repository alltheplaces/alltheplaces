from locations.storefinders.woosmap import WoosmapSpider


class BricoferITSpider(WoosmapSpider):
    name = "bricofer_it"
    item_attributes = {"brand": "Bricofer", "brand_wikidata": "Q126012596"}
    key = "woos-be159326-28cf-36ca-b940-616359889dba"
    origin = "https://www.bricofer.it"
