from scrapy.http import Response

from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class NilleNOSpider(JSONBlobSpider):
    name = "nille_no"
    item_attributes = {"brand": "Nille", "brand_wikidata": "Q11991429"}
    start_urls = ["https://www.nille.no/api/store-list/by-query?query="]
    needs_json_request = True
    locations_key = ["stores"]

    def post_process_item(self, item: Feature, response: Response, store: dict, **kwargs):
        if store.get("permanentlyClosed"):
            return

        item["branch"] = item.pop("name").removeprefix("Nille").strip()
        item["street_address"] = item.pop("street")

        if url_path := store.get("url"):
            item["website"] = response.urljoin(url_path)

        if main_image := store.get("mainImage"):
            if isinstance(main_image, dict) and not main_image.get("isFallbackImage"):
                if src := main_image.get("src"):
                    item["image"] = response.urljoin(src)

        if location_hours := store.get("workingHours"):
            opening_hours = OpeningHours()
            for day_hours in location_hours:
                day = DAYS_FROM_SUNDAY[day_hours["weekDay"]]
                if day_hours.get("closed"):
                    opening_hours.set_closed(day)
                else:
                    opening_hours.add_range(day, day_hours.get("startTime"), day_hours.get("endTime"))
            item["opening_hours"] = opening_hours

        yield item
