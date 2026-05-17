from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class TelenorNOSpider(JSONBlobSpider):
    name = "telenor_no"
    item_attributes = {"brand": "Telenorbutikken", "brand_wikidata": "Q845632"}
    start_urls = ["https://store.telenor.no/omnichannel/v1/dealers/search?isConsumer=true&limit=100"]
    needs_json_request = True

    def post_process_item(self, item: Feature, response: Response, store: dict, **kwargs):
        item["ref"] = store.get("storeId") or item.get("id")  # Prefer storeId over id for ref
        item["branch"] = item.pop("name").removeprefix("Telenorbutikken ").strip()

        if address := store.get("address"):
            item["city"] = address.get("postalArea")
            if shopping_centre := address.get("shoppingCentre"):
                item["located_in"] = shopping_centre

        if name := store.get("name"):
            slug = name.casefold()
            slug = slug.removeprefix("telenorbutikken").strip()
            slug = slug.translate(str.maketrans({"ø": "o", "æ": "ae", "å": "aa"}))
            slug = "-".join(slug.split())
            item["website"] = f"https://www.telenor.no/telenorbutikken/{slug}"

        if opening_hours := store.get("openingHours"):
            item["opening_hours"] = OpeningHours()
            if week_days := opening_hours.get("weekDays"):
                opening_time = week_days.get("openingTime")
                closing_time = week_days.get("closingTime")
                if opening_time and closing_time:
                    item["opening_hours"].add_days_range(DAYS_WEEKDAY, opening_time, closing_time, "%H.%M")
            if saturday := opening_hours.get("saturday"):
                opening_time = saturday.get("openingTime")
                closing_time = saturday.get("closingTime")
                if opening_time and closing_time:
                    item["opening_hours"].add_range("Sa", opening_time, closing_time, "%H.%M")

        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item
