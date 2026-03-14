from locations.storefinders.traveliq import TravelIQSpider


class NevadaDepartmentOfTransportationUSSpider(TravelIQSpider):
    name = "nevada_department_of_transportation_us"
    item_attributes = {
        "operator": "Nevada Department of Transportation",
        "operator_wikidata": "Q886390",
    }
    api_endpoint = "https://www.nvroads.com/api/v2/"
    api_key = "d02d4d76733b454eafe1198279463766"
