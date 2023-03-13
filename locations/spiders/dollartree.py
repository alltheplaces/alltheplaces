from locations.storefinders.where2getit import Where2GetItSpider


class DollarTreeSpider(Where2GetItSpider):
    name = "dollartree"
    item_attributes = {"brand": "Dollar Tree", "brand_wikidata": "Q5289230"}
    w2gi_id = "134E9A7A-AB8F-11E3-80DE-744E58203F82"
    w2gi_filter = {
        "icon": {"eq": ""},
        "ebt": {"eq": ""},
        "crafters_square": {"eq": ""},
        "freezers": {"eq": ""},
        "snack_zone": {"eq": ""},
    }
    w2gi_query = "CA"
