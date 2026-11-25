from typing import AsyncIterator, Iterable
from urllib.parse import parse_qs, urlparse

from scrapy import Selector
from scrapy.http import FormRequest, TextResponse

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

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(self.start_urls[0], formdata={"action": "get_all_stores_location", "nonce": ""})

    def pre_process_data(self, feature: dict) -> None:
        selector = Selector(text=feature["contentString"])
        feature["website"] = selector.xpath('//a[normalize-space(.)="View More"]/@href').get()

        url = urlparse(feature["website"])
        feature["ref"] = parse_qs(url.query)["p"][0] if url.query else url.path.strip("/").split("/")[-1]
        feature["address"] = merge_address_lines(selector.xpath('//p[contains(@class, "mb-2")]/a//text()').getall())
        feature["phone"] = selector.xpath('//a[starts-with(@href, "tel:")]/text()').get()

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        hours = OpeningHours()
        for row in Selector(text=feature["contentString"]).xpath("//ul/li"):
            hours.add_ranges_from_string(" ".join(row.xpath("./span//text()").getall()))

        item["opening_hours"] = hours
        apply_category(Categories.SHOP_TYRES, item)

        yield item
