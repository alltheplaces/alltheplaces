from scrapy.selector import Selector

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import CLOSED_IT, DAYS_IT, NAMED_DAY_RANGES_IT, NAMED_TIMES_IT, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class LaPiadineriaSpider(JSONBlobSpider):
    name = "la_piadineria"
    item_attributes = {
        "brand": "La Piadineria",
        "brand_wikidata": "Q108195414",
    }
    start_urls = ["https://www.lapiadineria.com/assets/js/dati/it/storelocator.json"]

    def pre_process_data(self, location):
        location.update(location.get("detail", {}))

    def post_process_item(self, item, response, location):
        if item["ref"] == "filtri":
            return None
        item["branch"], item["name"] = item["name"], None
        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "piadina"

        apply_yes_no("takeaway", item, "service_Asporto" in location.get("tag_servizi"))
        if delivery := location.get("tag_delivery").strip():
            item["extras"]["delivery:partner"] = ";".join(delivery.replace("delivery_", "").split())
        self.set_opening_hours(item, location)

        yield item

    def set_opening_hours(self, item, location):
        times = " ".join(Selector(text=location["times"]).css("li *::text").getall())
        if times:
            oh = OpeningHours()
            oh.add_ranges_from_string(
                times,
                days=DAYS_IT,
                named_day_ranges=NAMED_DAY_RANGES_IT,
                named_times=NAMED_TIMES_IT,
                closed=CLOSED_IT,
            )
            item["opening_hours"] = oh
