import chompjs
from scrapy import Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES


class KFCGRSpider(Spider):
    name = "kfc_gr"
    item_attributes = KFC_SHARED_ATTRIBUTES
    start_urls = ["https://www.kfc.gr/en/stores"]

    def parse(self, response, **kwargs):
        for store in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "locations")]/text()').re_first(r"locations\"[\s:]+(\[.+\]),")
        ):
            item = DictParser.parse(store)
            item["street_address"] = item.pop("addr_full")
            item["website"] = response.url
            apply_yes_no(Extras.TAKEAWAY, item, store["takeaway"])
            apply_yes_no(Extras.INDOOR_SEATING, item, store["sit_in"])
            yield item
