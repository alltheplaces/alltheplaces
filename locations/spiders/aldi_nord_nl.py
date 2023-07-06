from locations.storefinders.uberall import UberallSpider


class AldiNordNLSpider(UberallSpider):
    name = "aldi_nord_nl"
    item_attributes = {"brand": "ALDI", "brand_wikidata": "Q41171373"}
    key = "ALDINORDNL_8oqeY3lnn9MTZdVzFn4o0WCDVTauoZ"
