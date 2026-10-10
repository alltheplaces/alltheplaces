from typing import Iterable

import chompjs
from scrapy.http import TextResponse

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.hours import CLOSED_FR, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS

# Exact postcodes take precedence: Saint-Martin and Saint-Barthélemy share the 971 prefix.
OVERSEAS_POSTCODE_COUNTRIES = {
    "97150": "MF",
    "97133": "BL",
    "971": "GP",
    "972": "MQ",
    "973": "GF",
    "974": "RE",
    "975": "PM",
    "976": "YT",
    "986": "WF",
    "987": "PF",
    "988": "NC",
}


class PimkieFRSpider(JSONBlobSpider, CamoufoxSpider):
    name = "pimkie_fr"
    item_attributes = {"brand": "Pimkie", "brand_wikidata": "Q1758066", "name": "Pimkie"}
    start_urls = ["https://www.pimkie.fr/pages/magasins"]
    # Plain requests were observed to get a Shopify 500, then a Cloudflare managed challenge.
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS

    def extract_json(self, response: TextResponse) -> list[dict]:
        return chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "window.storelocator")]/text()').get("")
        )["stores"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if (feature.get("name") or "").strip().startswith("E-COMMERCE") or not feature.get("url"):
            return
        item["ref"] = feature["url"].rsplit("/", 1)[1]
        if branch := item.pop("name"):
            item["branch"] = branch.strip().title()
        item["street_address"] = item.pop("street")
        if city := item["city"]:
            item["city"] = city.split(" (")[0].title()
        item["website"] = response.urljoin(feature["url"])

        postcode = item["postcode"] or ""
        if country := OVERSEAS_POSTCODE_COUNTRIES.get(postcode) or OVERSEAS_POSTCODE_COUNTRIES.get(postcode[:3]):
            item["country"] = country
            # The NSI entry doesn't cover the overseas territories.
            apply_category(Categories.SHOP_CLOTHES, item)
            apply_category({"clothes": "women"}, item)

        # "am" holds each day's full range ("pm" is always blank); "FERME - FERME" is a closed day.
        # No hours at all when a day is half "FERME" (ambiguous, e.g. "FERME - 19:00") or when
        # every day is "FERME" (hours not entered). Malformed hours drop the hours, not the store.
        try:
            ranges = {day: times["am"].split(" - ") for day, times in feature["opening_hours"].items()}
            closed_counts = [times.count("FERME") for times in ranges.values()]
            if 1 not in closed_counts and set(closed_counts) != {2}:
                oh = OpeningHours()
                for day, (open_time, close_time) in ranges.items():
                    oh.add_range(day, open_time, close_time, closed=CLOSED_FR)
                item["opening_hours"] = oh
        except (AttributeError, KeyError, TypeError, ValueError):
            self.logger.warning(f"Unparsed opening hours for store {item['ref']}: {feature.get('opening_hours')}")

        yield item
