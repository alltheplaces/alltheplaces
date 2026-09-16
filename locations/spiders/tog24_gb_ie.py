from typing import Iterable

from scrapy import Selector
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class Tog24GBIESpider(JSONBlobSpider):
    name = "tog24_gb_ie"
    item_attributes = {"brand": "TOG24", "brand_wikidata": "Q131273719"}
    start_urls = [
        "https://www.tog24.com/apps/store-locator/stores/surrounding?shop=tog24.myshopify.com&latitude=54&longitude=-2&max_distance=0&limit=0"
    ]
    locations_key = "stores"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        sel = Selector(text=feature["summary"])
        item["branch"] = sel.xpath('//*[@class="sl-store-name"]/text()').get("").removeprefix("TOG24").strip()
        if "Stockist" in item["branch"]:
            return
        item["addr_full"] = clean_address(sel.xpath('//*[contains(@class, "sl-layout-line--address")]/text()').getall())
        item["phone"] = sel.xpath('//*[contains(@class, "sl-layout-line--phone")]/text()').get()
        item["email"] = sel.xpath('//*[contains(@class, "sl-layout-line--email")]/text()').get()
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            "; ".join(sel.xpath('//*[contains(@class, "sl-working-hours-legacy-row")]/text()').getall())
        )
        apply_category(Categories.SHOP_OUTDOOR, item)
        yield item
