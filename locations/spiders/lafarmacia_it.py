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
    dataset_attributes = AlgoliaSpider.dataset_attributes | {"website": "https://www.lafarmacia.it/trova-farmacia"}

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["storeCode"]
        item["name"] = feature["storeName"]
        item["street_address"] = feature["address"]
        item["city"] = feature["city"]
        item["postcode"] = feature["zipCode"]
        item["state"] = feature.get("region", "")
        item["phone"] = feature.get("phoneNumber")
        item["email"] = feature.get("email")
        item["website"] = f"https://www.lafarmacia.it/farmacia/{feature['slug']}"
        item["lat"] = feature["_geoloc"]["lat"]
        item["lon"] = feature["_geoloc"]["lng"]
        item.pop("addr_full", None)

        if whatsapp := feature.get("whatsapp", "").strip():
            set_social_media(item, SocialMedia.WHATSAPP, "+39" + whatsapp)

        oh = OpeningHours()
        for entry in feature.get("timetable", []):
            for h in entry.get("hours", []):
                oh.add_range(entry["weekday"].title(), h["openingTime"], h["closingTime"])
        item["opening_hours"] = oh

        apply_category(Categories.PHARMACY, item)
        item["extras"]["dispensing"] = "yes"

        yield item
