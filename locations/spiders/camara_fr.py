from scrapy.http import FormRequest

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_FR, DAYS_FR, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class CamaraFrSpider(JSONBlobSpider):
    name = "camara_fr"
    item_attributes = {
        "brand": "Camara",
        "brand_wikidata": "Q2930917",
    }

    locations_key = ["data", "stores"]

    async def start(self):
        yield FormRequest(
            url="https://www.camara.net/module/antstore/storeLocator",
            method="POST",
            formdata={
                "action": "getStores",
                "id_lang": "1",
                "modal": "0",
                "full": "1",
            },
            callback=self.parse,
        )

    def post_process_item(self, item, response, location):
        apply_category(Categories.SHOP_PHOTO, item)
        item["branch"] = item.pop("name", "").removeprefix("CAMARA ").lower()

        item["opening_hours"] = OpeningHours()
        for d in location.get("business_hours", []):
            item["opening_hours"].add_ranges_from_string(
                d.get("day", "") + " " + " ".join(d.get("hours", "")).replace("h", ":"), DAYS_FR, closed=CLOSED_FR
            )

        yield item
