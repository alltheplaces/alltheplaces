import json
import re

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_FR, DAYS_FR, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class AntonelleFRSpider(JSONBlobSpider):
    name = "antonelle_fr"
    item_attributes = {
        "brand": "Antonelle",
        "brand_wikidata": "Q105082567",
    }
    start_urls = ["https://www.antonelle.fr/magasins/"]

    def extract_json(self, response):
        data = response.xpath('//script[@id="stores-data"]/text()').get()
        if not data:
            raise ValueError("#stores-data not found")

        data = json.loads(data)
        return data

    def post_process_item(self, item, response, location):
        apply_category(Categories.SHOP_CLOTHES, item)
        item["branch"] = item.pop("name", "").removeprefix("Antonelle ")

        item["opening_hours"] = OpeningHours()
        for day in location.get("hours") or []:

            if day.get("hours")[0] == "":
                day.get("hours")[0] = "fermé"

            # Bare hour-only values like "10h" have no minutes component, so a
            # plain "h" -> ":" replace leaves a dangling "10:" the parser can't
            # read (e.g. "10h-13h" -> "10:-13:"), silently discarding the whole
            # day. Normalize those to "10:00" first; minute-bearing values like
            # "10h30" are unaffected since the (?!\d) lookahead skips them.
            hours_text = re.sub(r"(\d{1,2})h(?!\d)", r"\1:00", day.get("hours")[0]).replace("h", ":")

            results = OpeningHours.extract_hours_from_string(
                day.get("day") + " " + hours_text, DAYS_FR, closed=CLOSED_FR
            )

            if len(results) == 0:  # a day could not be parsed, no opening_hours will be added on this shop
                item["opening_hours"] = None
                break

            for result in results:
                for day in result[0]:
                    item["opening_hours"].add_range(day, result[1], result[2], closed=CLOSED_FR)

        yield item
