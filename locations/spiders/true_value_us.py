from locations.storefinders.where2getit import Where2GetItSpider


class TrueValueUSSpider(Where2GetItSpider):
    name = "true_value_us"
    item_attributes = {"brand": "True Value", "brand_wikidata": "Q7847545"}
    api_brand_name = "truevalue"
    api_key = "EDF319D8-F561-11E7-9BF7-BFAAF3F4F7A7"
    api_filter = {
        "and": {
            "truevaluebranded": {"eq": "Branded"},
            "excluded": {"distinctfrom": "1"},
            "active": {"eq": "1"},
        }
    }
