import re

from locations.categories import Extras, apply_category, apply_yes_no
from locations.json_blob_spider import JSONBlobSpider


class EssexUSSpider(JSONBlobSpider):
    name = "essex_us"
    start_urls = ["https://www.essexapartmenthomes.com/EPT_Feature/Search/GetSearchResults"]
    item_attributes = {
        "operator": "Essex",
        "operator_wikidata": "Q134703255",
    }
    locations_key = "communities"

    def post_process_item(self, item, response, feature):
        item["image"] = feature["imagelist"].split("|")[0]
        item["street_address"] = item.pop("addr_full")
        item["lat"], item["lon"] = feature["coordinate"].split(",")
        city_slug = re.sub(r"\W+", "-", feature["city"]).lower()
        item["website"] = f"https://www.essexapartmenthomes.com/apartments/{city_slug}/{feature['itemname']}"

        amenities = feature["communityamenities"].split("|")
        apply_yes_no(Extras.PETS_ALLOWED, item, "Pet friendly" in amenities)
        apply_yes_no(Extras.SWIMMING_POOL, item, "Swimming pool" in amenities)

        apply_category({"landuse": "residential", "residential": "apartments"}, item)

        yield item
