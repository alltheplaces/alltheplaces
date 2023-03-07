from locations.storefinders.uberall import UberallSpider


class AldiNordPLSpider(UberallSpider):
    name = "aldi_nord_pl"
    item_attributes = {"brand": "ALDI", "brand_wikidata": "Q41171373"}
    key = "ALDINORDPL_3Lul0K0H0Vy47Jz0wGZlN30mchboaO"
