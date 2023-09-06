import collections
import re

from scrapy.http import JsonRequest
from scrapy.spiders import XMLFeedSpider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class KFCNZSpider(XMLFeedSpider):
    name = "kfc_nz"
    item_attributes = {"brand": "KFC", "brand_wikidata": "Q524757"}
    allowed_domains = ["kfc.co.nz"]
    start_urls = ["https://kfc.co.nz/sitemap.xml"]
    itertag = "loc"
    requires_proxy = True

    def parse_node(self, response, node):
        url = node.xpath("//text()").get()
        if m := re.match(r"^https:\/\/kfc.co.nz\/find-a-kfc\/kfc-(.+)$", url):
            yield JsonRequest(url="https://api.kfc.co.nz/find-a-kfc/kfc-" + m.group(1), callback=self.parse_store)

    def parse_store(self, response):
        location = response.json()
        item = DictParser.parse(location)
        item.pop("addr_full")
        item["street_address"] = location["address"]
        item.pop("state")
        item["website"] = "https://kfc.co.nz/find-a-kfc/" + item["website"]

        apply_yes_no(Extras.DRIVE_THROUGH, item, location["drivethru"], False)
        apply_yes_no(Extras.DELIVERY, item, "delivery" in location["dispositions"], False)

        item["opening_hours"] = OpeningHours()
        day_list = collections.deque(DAYS.copy())
        day_list.rotate(1)
        for hours_range in location["operatingHoursStore"]:
            item["opening_hours"].add_range(
                day_list[int(hours_range["dayOfWeek"])], hours_range["start"], hours_range["end"]
            )

        yield item
