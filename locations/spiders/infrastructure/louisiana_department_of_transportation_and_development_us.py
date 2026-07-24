from locations.storefinders.traveliq_web_cameras import TravelIQWebCamerasSpider


class LouisianaDepartmentOfTransportationAndDevelopmentUSSpider(TravelIQWebCamerasSpider):
    name = "louisiana_department_of_transportation_and_development_us"
    item_attributes = {
        "operator": "Louisiana Department of Transportation & Development",
        "operator_wikidata": "Q2400783",
        "state": "LA",
    }
    allowed_domains = ["511la.org"]
