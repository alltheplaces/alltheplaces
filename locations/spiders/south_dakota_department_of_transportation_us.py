from locations.storefinders.clearroute import ClearRouteSpider


class SouthDakotaDepartmentOfTransportationUSSpider(ClearRouteSpider):
    name = "south_dakota_department_of_transportation_us"
    item_attributes = {"operator": "South Dakota Department of Transportation", "operator_wikidata": "Q5570193"}
    customer_id = "sd"
