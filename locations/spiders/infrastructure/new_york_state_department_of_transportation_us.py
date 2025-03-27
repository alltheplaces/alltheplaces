from locations.storefinders.traveliq import TravelIQSpider


class NewYorkStateDepartmentOfTransportationUSSpider(TravelIQSpider):
    name = "new_york_state_department_of_transportation_us"
    item_attributes = {
        "operator": "New York State Department of Transportation",
        "operator_wikidata": "Q7013447",
        "state": "NY",
    }
    api_endpoint = "https://511ny.org/api/v2/"
    api_key = "4e583b21f378403cb1532ba221366911"
