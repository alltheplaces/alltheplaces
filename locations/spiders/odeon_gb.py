from typing import Iterable

from scrapy.http import Response

from locations.camoufox_spider import CamoufoxSpider
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE


class OdeonGBSpider(JSONBlobSpider, CamoufoxSpider):
    name = "odeon_gb"
    item_attributes = {"brand": "Odeon", "brand_wikidata": "Q6127470"}
    start_urls = [
        "https://www.odeon.co.uk/api/omnia/v1/pageList?friendly=/cinemas/&properties=vistaCinema&properties=addressLine1&properties=addressLine2&properties=addressLine3&properties=latitude&properties=longitude&properties=postCode&properties=foodAndBeverageEnabled"
    ]
    captcha_type = "cloudflare_turnstile"
    captcha_selector_indicating_success = '//link[@href="resource://content-accessible/plaintext.css"]'
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
    handle_httpstatus_list = [403]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("alias") == "closedCinema":
            return
        item["ref"] = feature["vistaCinema"]["key"]
        item["addr_full"] = merge_address_lines(
            [
                feature.get("addressLine1"),
                feature.get("addressLine2"),
                feature.get("addressLine3"),
                feature.get("addressLine4"),
            ]
        )
        item["website"] = "https://www.odeon.co.uk" + feature["url"]
        yield item
