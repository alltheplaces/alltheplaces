import re

from chompjs import parse_js_object

from locations.categories import Categories, Clothes, apply_clothes
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class HallensteinBrothersAUNZSpider(JSONBlobSpider):
    name = "hallenstein_brothers_au_nz"
    item_attributes = {
        "brand": "Hallenstein Brothers",
        "brand_wikidata": "Q24189399",
        "extras": Categories.SHOP_CLOTHES.value,
    }
    allowed_domains = ["www.hallensteins.com"]
    start_urls = ["https://www.hallensteins.com/store-locations/all-stores-worldwide"]

    def extract_json(self, response):
        js_blob = (
            response.xpath('//script[contains(text(), "var ga_stores = ")]/text()')
            .get()
            .split("var ga_stores = ", 1)[1]
            .split("; // all store data", 1)[0]
        )
        return parse_js_object(js_blob)

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name", None)
        item["addr_full"] = re.sub(r"\s+", " ", item["addr_full"]).strip()

        state_urlsafe = re.sub(r"\s+", "-", feature["region"].lower().strip())
        name_urlsafe = re.sub(r"\s+", "-", feature["name"].lower().strip())
        item["website"] = "https://www.hallensteins.com/store-locations/{}/{}".format(state_urlsafe, name_urlsafe)

        if hours_string := feature.get("openinghours"):
            hours_string = re.sub(r"\s+", " ", hours_string)
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)

        apply_clothes([Clothes.MEN], item)

        yield item
