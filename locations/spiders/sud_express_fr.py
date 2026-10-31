import re
from typing import Iterable

import chompjs
from scrapy.http import Response, TextResponse

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SudExpressFRSpider(JSONBlobSpider):
    name = "sud_express_fr"
    item_attributes = {"brand": "Sud Express", "brand_wikidata": "Q104826254", "name": "Sud Express"}
    allowed_domains = ["www.sudexpress.fr"]
    start_urls = ["https://www.sudexpress.fr/pages/decouvrez-nos-adresses"]
    name_is_branch = True

    def extract_json(self, response: TextResponse) -> list[dict]:
        return chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "window.storelocator")]/text()').get("")
        )["stores"]

    def pre_process_data(self, feature: dict) -> None:
        # "street" includes the house number
        if address := feature.get("address"):
            address["street_address"] = address.pop("street", None)

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable:
        if not (page_url := feature.get("page_url")):
            self.logger.warning(f"Skipping store without page_url: {feature.get('name')}")
            return
        item["ref"] = page_url.rsplit("/", 1)[-1]
        item["website"] = response.urljoin(page_url)
        item["branch"] = re.sub(r"(?i)^sud express\s*", "", item.get("branch") or "").strip() or None
        apply_category(Categories.SHOP_CLOTHES, item)
        apply_yes_no("factory_outlet", item, feature.get("is_outlet", False))
        # Opening hours are only published on each store page
        yield response.follow(
            item["website"], self.parse_store_page, cb_kwargs={"item": item}, errback=self.store_page_failed
        )

    def store_page_failed(self, failure) -> Iterable[Feature]:
        yield failure.request.cb_kwargs["item"]

    def parse_store_page(self, response: Response, item: Feature) -> Iterable[Feature]:
        oh = OpeningHours()
        # Exact label match, so the "Horaires Exceptionnels" (dated closures) block is skipped
        for row in response.xpath('//span[normalize-space()="Horaires"]/following-sibling::div[1]/div'):
            if not (day := sanitise_day(row.xpath("normalize-space(span[1])").get(""), DAYS_FR)):
                continue
            # e.g. "10h - 19h", "9h30 - 12h et 14h30 - 19h"
            for open_h, open_m, close_h, close_m in re.findall(
                r"(\d{1,2})\s*[h:]\s*([0-5]\d)?\s*[-–—]\s*(\d{1,2})\s*[h:]\s*([0-5]\d)?",
                row.xpath("normalize-space(span[2])").get(""),
            ):
                oh.add_range(day, f"{open_h}:{open_m or '00'}", f"{close_h}:{close_m or '00'}")
        item["opening_hours"] = oh
        yield item
