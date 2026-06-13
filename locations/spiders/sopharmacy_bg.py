from typing import Iterable

from scrapy.http import Response

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.hours import DAYS_BG, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_INTERSTITIAL


class SopharmacyBGSpider(JSONBlobSpider, CamoufoxSpider):
    name = "sopharmacy_bg"
    item_attributes = {"brand": "SOpharmacy", "brand_wikidata": "Q108852081"}
    allowed_domains = ["sopharmacy.bg"]
    start_urls = ["https://sopharmacy.bg/bg/mapbox/contactus.json"]
    locations_key = ["contact-map", "features"]
    captcha_type = "cloudflare_interstitial"
    captcha_selector_indicating_success = '//link[@href="resource://content-accessible/plaintext.css"]'
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_INTERSTITIAL
    handle_httpstatus_list = [403]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))
        feature.update(feature.pop("contacts"))
        try:
            # Coordinates are supplied as strings not floating point numbers.
            # Attempt converstion to floating point numbers.
            feature["geometry"]["coordinates"][0] = float(feature["geometry"]["coordinates"][0])
            feature["geometry"]["coordinates"][1] = float(feature["geometry"]["coordinates"][1])
        except ValueError:
            pass

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        item["street_address"] = item.pop("addr_full", None)
        item["opening_hours"] = OpeningHours()
        for day_hours in feature["worktime"]:
            item["opening_hours"].add_ranges_from_string(day_hours, DAYS_BG)
        apply_category(Categories.PHARMACY, item)
        yield item
