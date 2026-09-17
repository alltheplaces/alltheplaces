import chompjs

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class QuickBELUSpider(JSONBlobSpider):
    name = "quick_be_lu"
    item_attributes = {"brand": "Quick", "brand_wikidata": "Q286494"}
    allowed_domains = ["www.quick.be"]
    start_urls = ["https://www.quick.be/fr/restaurants"]

    def extract_json(self, response):
        return chompjs.parse_js_object(response.xpath('//script[@id="__NEXT_DATA__"]//text()').get())["props"][
            "pageProps"
        ]["restaurants"]

    def post_process_item(self, item, response, location):
        apply_category(Categories.FAST_FOOD, item)
        item["branch"] = item.pop("name", "")
        item["lat"] = location["latlng"]["lat"]
        item["lon"] = location["latlng"]["lng"]
        item["street_address"] = item.pop("addr_full")
        item["country"] = "BE"
        if location["country_luxembourg"]:
            item["country"] = "LU"
        item["website"] = "https://www.quick.be/fr/restaurant/" + location["slug"]
        item["opening_hours"] = OpeningHours()
        for day in location["opening_hours"]:
            if day["opening_type"] != 1:
                continue
            item["opening_hours"].add_range(DAYS[day["weekday_from"] - 1], day["from_hour"], day["to_hour"], "%H:%M:%S")

        if postcode := item.get("postcode"):
            item["postcode"] = str(postcode)

        yield item
