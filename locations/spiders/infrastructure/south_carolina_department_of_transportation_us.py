from locations.storefinders.clearroute import ClearRouteSpider


class SouthCarolinaDepartmentOfTransportationUSSpider(ClearRouteSpider):
    name = "south_carolina_department_of_transportation_us"
    item_attributes = {"operator": "South Carolina Department of Transportation", "operator_wikidata": "Q5569993"}
    customer_id = "sc"
    features = ["cameras"]
