from locations.storefinders.clearroute import ClearRouteSpider


class MontanaDepartmentOfTransportationUSSpider(ClearRouteSpider):
    name = "montana_department_of_transportation_us"
    item_attributes = {"operator": "Montana Department of Transportation", "operator_wikidata": "Q5558259"}
    customer_id = "mt"
