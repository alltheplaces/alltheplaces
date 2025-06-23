import re
from typing import Iterable

from scrapy import Selector
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, DAYS_CZ
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class BrnenkaCZSpider(JSONBlobSpider):
    name = "brnenka_cz"
    item_attributes = {"brand": "Brněnka", "brand_wikidata": "Q14594510"}
    allowed_domains = ["www.brnenka.cz"]
    start_urls = ["http://www.brnenka.cz/prodejny/?do=map-markers"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        details_html = Selector(text=feature["message"])
        item["ref"] = details_html.xpath('//a[contains(@href, "/detail-prodejny/")]/@href').get().split("/")[2]
        item["lat"] = feature["position"][0]
        item["lon"] = feature["position"][1]
        item["website"] = "http://www.brnenka.cz/detail-prodejny/" + details_html.xpath('//a[contains(@href, "/detail-prodejny/")]/@href').get().split("/")[2]
        item["addr_full"] = merge_address_lines(details_html.xpath('//p[@class="address"]//text()').getall())
        hours_text = " ".join(details_html.xpath('//table[@class="opening"]//text()').getall())
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_text, days=DAYS_CZ, delimiters=["−"])
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
