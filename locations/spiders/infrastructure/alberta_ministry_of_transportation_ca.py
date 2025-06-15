from locations.storefinders.traveliq import TravelIQSpider


class AlbertaMinistryOfTransportationCASpider(TravelIQSpider):
    name = "alberta_ministry_of_transportation_ca"
    item_attributes = {
        "operator": "Alberta Ministry of Transportation",
        "operator_wikidata": "Q15058324",
    }
    api_endpoint = "https://511.alberta.ca/api/v2/"
    api_key = "production_key"
