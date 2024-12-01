from locations.storefinders.traveliq_web_cameras import TravelIQWebCamerasSpider


class ConnecticutDepartmentOfTransportationUSSpider(TravelIQWebCamerasSpider):
    name = "connecticut_department_of_transportation_us"
    allowed_domains = ["www.ctroads.org"]
    operators = {
        "ConnDOT": ["Connecticut Department of Transportation", "Q4923420", "CT"]
    }
