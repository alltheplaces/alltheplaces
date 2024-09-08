from scrapy.http import JsonRequest

from locations.hours import DAYS_FULL, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.sunglass_hut_1 import SUNGLASS_HUT_SHARED_ATTRIBUTES

SUNGLASS_HUT_4_COUNTRIES = {
    "HK": 8,
    "PT": 4,
    "TR": 6,
    "MENA": 11,  # Algeria, Bahrain, Cyprus, Egypt, Jordan, KSA, Kuwait, Lebanon, Oman, Qatar, UAE
}


class SunglassHut2Spider(JSONBlobSpider):
    name = "sunglass_hut_2"
    item_attributes = SUNGLASS_HUT_SHARED_ATTRIBUTES
    locations_key = "contentlets"

    def start_requests(self):
        for cc, lang_id in SUNGLASS_HUT_4_COUNTRIES.items():
            yield JsonRequest(
                url=f"https://{cc}.sunglasshut.com/api/content/render/false/limit/9999/type/json/query/+contentType:SghStoreLocator%20+languageId:{lang_id}",
                callback=self.parse,
                meta={"country": cc},
            )

    def post_process_item(self, item, response, location):
        if response.meta["country"] == "MENA":
            item["country"] = location.get("innerCountry")
        else:
            item["country"] = response.meta["country"]
        url_code = response.meta["country"].lower()
        if url_code == "mena":
            item["website"] = f"https://{url_code}.sunglasshut.com/en/store-locator/{location['seoUrl']}"
        else:
            item["website"] = f"https://{url_code}.sunglasshut.com/{url_code}/store-locator/{location['seoUrl']}"

        if item.get("state") is not None and item["state"].title() == "Namibia":
            item["country"] = item.pop("state")
        if item.get("state") is not None and item["state"].title() == "Portugal":
            item.pop("state")

        item["city"] = item["city"].replace("(China)", "").strip()
        item["branch"] = item.pop("name")
        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            item["opening_hours"].add_ranges_from_string(day + " " + location.get(day.lower()).replace(" : ", " - "))
        yield item
