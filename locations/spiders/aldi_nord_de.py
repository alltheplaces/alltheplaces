from locations.storefinders.uberall import UberallSpider


# Does have Linked Data, but requires JS to load it
class AldiNordDESpider(UberallSpider):
    name = "aldi_nord_de"
    item_attributes = {"brand": "ALDI Nord", "brand_wikidata": "Q41171373"}
    key = "ALDINORDDE_UimhY3MWJaxhjK9QdZo3Qa4chq1MAu"
