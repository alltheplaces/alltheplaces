from locations.storefinders.uberall import UberallSpider


class AldiNordESSpider(UberallSpider):
    name = "aldi_nord_es"
    item_attributes = {"brand": "ALDI", "brand_wikidata": "Q41171373"}
    key = "ALDINORDES_kRpYT2HM1bFjL9vTpn5q0JupSiXqnB"
