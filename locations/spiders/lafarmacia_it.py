from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature, SocialMedia, set_social_media
from locations.storefinders.algolia import AlgoliaSpider


class LafarmaciaITSpider(AlgoliaSpider):
    name = "lafarmacia_it"
    item_attributes = {"brand": "Lafarmacia.", "brand_wikidata": "Q131009869"}
    # Found in /_next/static/chunks/6569-*.js, Algolia client initialisation
    app_id = "WKANYZFMAK"
    api_key = "8b957ae6bfa82c42e761eb8dea2767bd"
    index_name = "prod_LAF_STORES"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if item["name"].startswith("Lafarmacia."):
            item["branch"] = item.pop("name").removeprefix("Lafarmacia.")
        elif item["name"].startswith("Dispensario Lafarmacia."):
            item["branch"] = (
                item.pop("name")
                .removeprefix("Dispensario Lafarmacia.")
                .replace("Dispensario", "")
                .replace("dispensario", "")
            )
            item["name"] = "Dispensario Lafarmacia."

        item["street_address"] = item.pop("addr_full", None)
        item["lat"] = feature["_geoloc"]["lat"]
        item["lon"] = feature["_geoloc"]["lng"]
        item["ref"] = feature["storeCode"]
        item["website"] = f"https://www.lafarmacia.it/farmacia/{feature['slug']}"

        if whatsapp := feature.get("whatsapp", "").strip():
            set_social_media(item, SocialMedia.WHATSAPP, "+39" + whatsapp)

        oh = OpeningHours()
        for entry in feature.get("timetable", []):
            for h in entry.get("hours", []):
                oh.add_range(entry["weekday"], h["openingTime"], h["closingTime"])
        item["opening_hours"] = oh

        apply_category(Categories.PHARMACY, item)

        yield item
