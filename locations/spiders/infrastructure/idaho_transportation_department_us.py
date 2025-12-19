from locations.storefinders.traveliq import TravelIQSpider


class IdahoTransportationDepartmentUSSpider(TravelIQSpider):
    name = "idaho_transportation_department_us"
    item_attributes = {
        "operator": "Idaho Transportation Department",
        "operator_wikidata": "Q4925016",
        "state": "ID",
    }
    api_endpoint = "https://511.idaho.gov/api/v2/"
    api_key = "864413d556b048baa68739d8575aa46d"
