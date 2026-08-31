from locations.storefinders.electrify_america import ElectrifyAmericaSpider


class ElectrifyAmericaUSSpider(ElectrifyAmericaSpider):
    name = "electrify_america_us"
    item_attributes = {"operator": "Electrify America", "operator_wikidata": "Q59773555"}
    domain = "electrifyamerica.com"
