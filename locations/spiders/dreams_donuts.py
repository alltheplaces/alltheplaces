from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.items import set_closed
import json

class DreamsDonutsSpider(JSONBlobSpider):
    name = "dreams_donuts"
    item_attributes = {
        "brand": "Dreams Donuts",
        "brand_wikidata": "Q141142873",
    }

    start_urls = ["https://boutiques.dreamsdonuts.com/"]

    def extract_json(self, response):
        data = response.css("script#__NEXT_DATA__::text").get()

        if not data:
            raise ValueError("__NEXT_DATA__ not found")

        data = json.loads(data)
        return data["props"]["pageProps"]["data"]["stores"]

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name", "").removeprefix("Dreams Donuts ")

        if location.get("businessStatus") == "CLOSED_PERMANENTLY":
            set_closed(item)

        if location.get("slug") is not None:
            item["website"] = "https://boutiques.dreamsdonuts.com/"+location.get("slug")

        item["opening_hours"] = OpeningHours()

        if location.get("openingHours") is not None:
            for day in location["openingHours"]:
                if (
                    day.get("openDay") is not None
                    and day.get("openTime") is not None
                    and day.get("closeTime") is not None
                    and day.get("openTime").get("hours") is not None
                    and day.get("closeTime").get("hours") is not None
                ):

                    openMinutes = day.get("openTime").get("minutes") or "00"
                    closeMinutes = day.get("closeTime").get("minutes") or "00"

                    item["opening_hours"].add_ranges_from_string(
                        day.get("openDay")
                        + " "
                        + str(day.get("openTime").get("hours"))
                        + ":"
                        + str(openMinutes)
                        + "-"
                        + str(day.get("closeTime").get("hours"))
                        + ":"
                        + str(closeMinutes)
                    )

        apply_category(Categories.SHOP_PASTRY, item)
        yield item
