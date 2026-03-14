from locations.storefinders.castle_rock_oneweb import CastleRockOneWebSpider


class NebraskaDepartmentOfTransportationUSSpider(CastleRockOneWebSpider):
    name = "nebraska_department_of_transportation_us"
    item_attributes = {
        "operator": "Nebraska Department of Transportation",
        "operator_wikidata": "Q16861277",
        "state": "NE",
    }
    api_endpoint = "https://www.511.nebraska.gov/api/graphql"
    custom_settings = {"ROBOTSTXT_OBEY": False}
