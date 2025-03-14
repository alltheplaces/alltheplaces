from locations.storefinders.traveliq import TravelIQSpider


class GovernmentOfYukonCASpider(TravelIQSpider):
    name = "government_of_yukon_ca"
    item_attributes = {
        "operator": "Government of Yukon",
        "operator_wikidata": "Q106497978",
    }
    api_endpoint = "https://511yukon.ca/api/v2/"
    api_key = "d5b873eff91d485b9985973a5a569bf6"
