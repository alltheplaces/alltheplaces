import re
from typing import Iterable

from scrapy import Selector
from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class AdvantageNZSpider(JSONBlobSpider):
    name = "advantage_nz"
    item_attributes = {"brand": "Advantage", "brand_wikidata": "Q131625974"}
    allowed_domains = ["advantagetyres.co.nz"]
    start_urls = ["https://advantagetyres.co.nz/wp/wp-admin/admin-ajax.php"]

    def start_requests(self) -> Iterable[FormRequest]:
        yield FormRequest(url=self.start_urls[0], formdata={"action": "get_all_stores_location", "nonce": ""})

    def pre_process_data(self, feature: dict) -> None:
        if not feature.get("contentString"):
            return None
        extra_attributes_selector = Selector(text=feature["contentString"])

        feature["name"] = extra_attributes_selector.xpath('//h4[@class="mb-2"]/text()').get().strip()
        feature["address"] = merge_address_lines(
            extra_attributes_selector.xpath('//p[@class="mb-2"]/a//text()').getall()
        )
        feature["phone"] = (
            extra_attributes_selector.xpath('//a[contains(@href, "tel:")]/@href').get().replace("tel:", "").strip()
        )
        feature["website"] = (
            extra_attributes_selector.xpath('//p/a[contains(@href, "https://advantagetyres.co.nz/store/")]/@href')
            .get()
            .strip()
        )
        feature["ref"] = feature["website"].split("/")[-2]

        hours_text = re.sub(
            r"\s+", " ", " ".join(extra_attributes_selector.xpath('//p[@class="mb-1"]//li//text()').getall())
        ).strip()
        feature["opening_hours"] = hours_text

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(feature.get("opening_hours", ""))

        apply_category(Categories.SHOP_TYRES, item)

        yield item
