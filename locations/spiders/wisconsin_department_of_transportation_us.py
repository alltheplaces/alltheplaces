from locations.storefinders.traveliq import TravelIQSpider


class WisconsinDepartmentOfTransportationUSSpider(TravelIQSpider):
    name = "wisconsin_department_of_transportation_us"
    item_attributes = {
        "operator": "Wisconsin Department of Transportation",
        "operator_wikidata": "Q8027162",
    }
    api_endpoint = "https://511wi.gov/api/v2/"
    api_key = "8205fb27b11949e995c89682f2ec85e8"
