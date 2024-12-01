from locations.storefinders.traveliq import TravelIQSpider


class GeorgiaDepartmentOfTransportationUSSpider(TravelIQSpider):
    name = "georgia_department_of_transportation_us"
    item_attributes = {
        "operator": "Georgia Department of Transportation",
        "operator_wikidata": "Q944993",
    }
    api_endpoint = "https://511ga.org/api/v2/"
    api_key = "b6ddda430bf94f08a565fd8912f10bbc"
