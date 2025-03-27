from locations.storefinders.traveliq import TravelIQSpider


class ArizonaDepartmentOfTransportationUSSpider(TravelIQSpider):
    name = "arizona_department_of_transportation_us"
    item_attributes = {
        "operator": "Arizona Department of Transportation",
        "operator_wikidata": "Q807704",
    }
    api_endpoint = "https://www.az511.com/api/v2/"
    api_key = "6a99a7698056435b836f2bd8a72b4249"
