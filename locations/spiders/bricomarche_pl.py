from typing import Iterable
from urllib.parse import urljoin

from scrapy.http import Response

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE


class BricomarchePLSpider(JSONBlobSpider, CamoufoxSpider):
    name = "bricomarche_pl"
    item_attributes = {"brand": "Bricomarché", "brand_wikidata": "Q2925147"}
    start_urls = ["https://www.bricomarche.pl/api/v1/pos/pos/poses.json"]
    locations_key = "results"
    captcha_type = "cloudflare_turnstile"
    captcha_selector_indicating_success = '//link[@href="resource://content-accessible/plaintext.css"]'
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
    handle_httpstatus_list = [403]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if slug := feature.get("Slug"):
            item["website"] = urljoin("https://www.bricomarche.pl/sklep/", slug)
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
