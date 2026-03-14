from locations.storefinders.traveliq import TravelIQSpider


class FloridaDepartmentOfTransportationUSSpider(TravelIQSpider):
    name = "florida_department_of_transportation_us"
    item_attributes = {
        "operator": "Florida Department of Transportation",
        "operator_wikidata": "Q3074270",
        "state": "FL",
    }
    api_endpoint = "https://fl511.com/api/v2/"
    api_key = "7bafc2d1931749e9b7933450c5aefd5d"
