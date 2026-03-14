from locations.storefinders.traveliq import TravelIQSpider


class UtahDepartmentOfTransportationUSSpider(TravelIQSpider):
    name = "utah_department_of_transportation_us"
    item_attributes = {
        "operator": "Utah Department of Transportation",
        "operator_wikidata": "Q2506783",
    }
    api_endpoint = "https://www.udottraffic.utah.gov/api/v2/"
    api_key = "7bafc2d1931749e9b7933450c5aefd5d"
