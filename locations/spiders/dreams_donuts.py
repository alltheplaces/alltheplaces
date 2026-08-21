from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class DreamsDonutsSpider(JSONBlobSpider):
    name = "dreams_donuts"
    item_attributes = {
        "brand": "Dreams Donuts",
        "brand_wikidata": "Q141142873",
    }
    start_urls = ["https://boutiques.dreamsdonuts.com/_next/data/0fZaY95cqqjf19_M8VcLX/index.json"]
    locations_key = ["pageProps", "data", "stores"]

    def post_process_item(self, item, response, location):
        item["name"] = "Dreams Donuts"

        oh = OpeningHours()

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

                    oh.add_ranges_from_string(
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

        item["opening_hours"] = oh
        apply_category(Categories.SHOP_PASTRY, item)
        yield item
