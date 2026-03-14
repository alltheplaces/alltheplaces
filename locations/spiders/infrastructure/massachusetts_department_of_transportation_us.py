from locations.storefinders.castle_rock_oneweb import CastleRockOneWebSpider


class MassachusettsDepartmentOfTransportationUSSpider(CastleRockOneWebSpider):
    name = "massachusetts_department_of_transportation_us"
    item_attributes = {
        "operator": "Massachusetts Department of Transportation",
        "operator_wikidata": "Q2483364",
        "state": "MA",
    }
    api_endpoint = "https://mass511.com/api/graphql"
    custom_settings = {"ROBOTSTXT_OBEY": False}
