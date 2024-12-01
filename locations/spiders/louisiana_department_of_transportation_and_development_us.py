from locations.storefinders.traveliq import TravelIQSpider


class LouisianaDepartmentOfTransportationAndDevelopmentUSSpider(TravelIQSpider):
    name = "louisiana_department_of_transportation_and_development_us"
    item_attributes = {
        "operator": "Louisiana Department of Transportation and Development",
        "operator_wikidata": "Q2400783",
    }
    api_endpoint = "https://511la.org/api/v2/"
    api_key = "7a43f543af71472db8ff3c01c84aea45"
