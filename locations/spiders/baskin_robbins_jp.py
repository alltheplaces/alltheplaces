from typing import Iterable

from scrapy.http import Response

from locations.categories import Extras, apply_yes_no
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.storefinders.location_cloud import LocationCloudSpider


class BaskinRobbinsJPSpider(LocationCloudSpider):
    name = "baskin_robbins_jp"
    item_attributes = {"brand_wikidata": "Q584601"}
    api_endpoint = "https://store.br31.jp/br31/api/proxy2/shop/list"
    website_formatter = "https://store.br31.jp/br31/spot/detail?code={}"

    def parse_detail_page(self, response: Response, item: Feature, source_feature: dict) -> Iterable[Feature]:
        ld = LinkedDataParser.find_linked_data(response, "LocalBusiness")
        item["phone"] = ld.get("telephone")
        item["opening_hours"] = LinkedDataParser.parse_opening_hours(ld)

        flags = set(response.xpath('//img[contains(@src, "/detail_image/")]/@alt').getall())
        apply_yes_no(Extras.PARKING, item, "駐車場" in flags)
        apply_yes_no(Extras.DELIVERY, item, bool({"Uber EatsのURL", "出前館のURL", "デリバリーのURL"} & flags))
        if "クレープ" in flags:
            item["extras"]["cuisine"] = "crepe"
        yield item

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = source_feature["name"].removeprefix("サーティワンアイスクリーム　")
        yield item
