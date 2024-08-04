from locations.hours import OpeningHours
from locations.storefinders.where2getit import Where2GetItSpider


class DollarTreeSpider(Where2GetItSpider):
    name = "dollar_tree"
    item_attributes = {"brand": "Dollar Tree", "brand_wikidata": "Q5289230"}
    api_brand_name = "dollartree"
    api_key = "134E9A7A-AB8F-11E3-80DE-744E58203F82"

    def parse_item(self, item, location):
        item["name"] = None
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(location.get("hours"))
        yield item
