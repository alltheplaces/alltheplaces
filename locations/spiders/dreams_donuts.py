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

        if location.get("openingHours") != None:
            print(str(location.get("openingHours")))

            for day in location["openingHours"]:
                if (
                    day.get("openDay") != None
                    and day.get("openTime") != None
                    and day.get("closeTime") != None
                    and day.get("openTime").get("hours") != None
                    and day.get("closeTime").get("hours") != None
                ):

                    openMinutes = day.get("openTime").get("minutes") or "00"
                    closeMinutes = day.get("openTime").get("minutes") or "00"

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

        print(oh.as_opening_hours())
        item["opening_hours"] = oh
        apply_category(Categories.SHOP_PASTRY, item)
        yield item
