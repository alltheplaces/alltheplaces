from typing import Any, Iterable

from scrapy.http import Request, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.storefinders.goga_store_locator import GogaStoreLocatorSpider


class BigechoJPSpider(GogaStoreLocatorSpider):
    name = "bigecho_jp"
    item_attributes = {"brand_wikidata": "Q15831707"}
    start_urls = ['https://shop.big-echo.jp/api/point?f=["短縮ＵＲＬ","電話番号"]']

    # Bit positions in __condition_flags, in the order of the "conditions" list on shop.big-echo.jp
    CONDITIONS = {
        7: Extras.PARKING,
        9: Extras.SMOKING_AREA,
        11: Extras.WHEELCHAIR,
        12: Extras.TOILETS_WHEELCHAIR,
        13: Extras.KIDS_AREA,
        18: Extras.WIFI,
    }

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Request]:
        item["website"] = source_feature["短縮ＵＲＬ"]
        apply_category(Categories.KARAOKE_BOX, item)
        for bit, attribute in self.CONDITIONS.items():
            apply_yes_no(attribute, item, source_feature["__condition_flags"] & 1 << bit)
        if source_feature["__condition_flags"] & 1 << 22:
            item["extras"]["sport"] = "darts"
        yield Request(item["website"], callback=self.parse_hours, cb_kwargs={"item": item})

    def parse_hours(self, response: Response, item: Feature, **kwargs: Any) -> Iterable[Feature]:
        item["opening_hours"] = LinkedDataParser.parse_opening_hours(
            LinkedDataParser.find_linked_data(response, "LocalBusiness")
        )
        yield item
