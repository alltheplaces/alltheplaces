import json
import re
from typing import Iterable

from scrapy import Selector
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

DAYS_SQ = {
    "E Hënë": "Mo",
    "E Martë": "Tu",
    "E Mërkurë": "We",
    "E Enjte": "Th",
    "E Premte": "Fr",
    "E Shtunë": "Sa",
    "E Diel": "Su",
}


class BpbXKSpider(JSONBlobSpider):
    name = "bpb_xk"
    item_attributes = {
        "brand": "Banka Për Biznes",
        "brand_wikidata": "Q16349919",
    }
    start_urls = ["https://bpbbank.com/wp-content/plugins/rrota-elementor/assets/js/branches.js"]

    def extract_json(self, response: Response) -> list[dict]:
        blob = re.search(r"const locations = JSON\.parse\('(.*)'\);", response.text).group(1)
        try:
            # Blob is served as doubly-encoded UTF-8, mangling Albanian diacritics.
            blob = blob.encode("latin-1").decode("utf-8")
        except UnicodeError:
            pass
        return json.loads(blob)

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        item.pop("name")  # title is address, not name
        item.pop("city")  # is not accurate
        item["ref"] = f"{location.get('title', '').replace(' ', '-')}-{location['type']}"
        item["addr_full"] = location["title"]

        opening_hours = OpeningHours()
        opening_hours.add_ranges_from_string(
            # Stray closing tag would otherwise run Saturday's hours into Friday's.
            " ".join(Selector(text=location["text"].replace("</br>", "<br/>")).xpath("//text()").getall()),
            days=DAYS_SQ,
        )
        if opening_hours:
            item["opening_hours"] = opening_hours

        if location["type"] == 1:
            apply_category(Categories.BANK, item)
        else:
            apply_category(Categories.ATM, item)
        yield item
