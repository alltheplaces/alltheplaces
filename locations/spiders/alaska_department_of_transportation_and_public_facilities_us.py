from locations.storefinders.traveliq import TravelIQSpider


class AlaskaDepartmentOfTransportationAndPublicFacilitiesUSSpider(TravelIQSpider):
    name = "alaska_department_of_transportation_and_public_facilities_us"
    item_attributes = {
        "operator": "Alaska Department of Transportation & Public Facilities",
        "operator_wikidata": "Q4708536",
    }
    api_endpoint = "https://511.alaska.gov/api/v2/"
    api_key = "7bafc2d1931749e9b7933450c5aefd5d"
