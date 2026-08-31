from locations.storefinders.electrify_america import ElectrifyAmericaSpider


class ElectrifyCanadaCASpider(ElectrifyAmericaSpider):
    name = "electrify_canada_ca"
    item_attributes = {"operator": "Electrify Canada", "operator_wikidata": "Q104844533"}
    domain = "electrify-canada.ca"
