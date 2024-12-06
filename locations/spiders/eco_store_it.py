import chompjs

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_IT, DAYS_EN, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class EcoStoreITSpider(JSONBlobSpider):
    name = "eco_store_it"
    item_attributes = {
        "brand": "Eco Store",
        "brand_wikidata": "Q126483871",
    }
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ["https://www.ecostore.it/wp-content/themes/pn-theme/models/services/stores/get-all-locations.json"]

    def post_process_item(self, item, response, location):
        if location["status"] != "1":
            return None
        apply_category(Categories.SHOP_PRINTER_INK, item)
        item["addr_full"] = location["formatted_address_loc"]
        yield response.follow(
            f'https://www.ecostore.it/store-locator/?id={item["ref"]}',
            cb_kwargs={"item": item},
            callback=self.parse_ld_json,
            errback=self.keep_less_data,
        )

    def keep_less_data(self, failure):
        return failure.request.cb_kwargs["item"]

    def parse_ld_json(self, response, item):
        if response.url == "https://www.ecostore.it/store-locator/":
            return item
        item["website"] = response.url
        obj = chompjs.parse_js_object(
            response.xpath("//script[@type=$ldjson]/text()", ldjson="application/ld+json").get()
        )
        oh = OpeningHours()
        for day in obj.get("openingHours"):
            oh.add_ranges_from_string(
                day,
                days=DAYS_EN,  # yes, days in english and closed in italian...
                closed=CLOSED_IT,
            )
        item["opening_hours"] = oh
        item["image"] = obj["image"]
        item["street_address"] = obj["address"].get("streetAddress")
        item["postcode"] = obj["address"].get("postalCode")
        item["city"] = obj["address"].get("addressLocality")
        item["branch"] = obj["description"]
        item["name"] = obj["name"]
        return item
