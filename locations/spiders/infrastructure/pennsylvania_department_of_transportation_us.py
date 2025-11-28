from locations.storefinders.traveliq import TravelIQSpider


class PennsylvaniaDepartmentOfTransportationUSSpider(TravelIQSpider):
    name = "pennsylvania_department_of_transportation_us"
    item_attributes = {
        "operator": "Pennsylvania Department of Transportation",
        "operator_wikidata": "Q5569650",
    }
    api_endpoint = "https://511pa.com/api/v2/"
    api_key = "7bafc2d1931749e9b7933450c5aefd5d"
