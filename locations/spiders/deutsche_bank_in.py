import re

import scrapy

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.deutsche_bank_be import DeutscheBankBESpider


class DeutscheBankINSpider(scrapy.Spider):
    name = "deutsche_bank_in"
    item_attributes = DeutscheBankBESpider.item_attributes
    start_urls = ["https://www.deutschebank.co.in/en/connect-with-us/atm-and-branch-locations.html"]

    def parse(self, response, **kwargs):
        locations_parent_node = response.xpath('//section[@class="acc__entry"]//section[@id]')
        for available_locations in [
            locations_parent_node.xpath("./p"),
            locations_parent_node.xpath("./div"),
            locations_parent_node.xpath('.//ul[@class="ul-dash"]/li'),
        ]:
            for location in available_locations:
                location_info = location.xpath("./text()").getall()
                if "cash dispenser" in location.get().lower():  # ATM
                    if match := re.search(r"ID[*\s:]+(\w+)", location.get()):
                        item = Feature()
                        item["ref"] = match.group(1)
                        item["addr_full"] = location_info[0].replace("Address", "").replace(":", "")
                        item["website"] = response.url
                        apply_category(Categories.ATM, item)
                        if "cheque deposit" in location.get().lower():
                            apply_yes_no("cheque_in", item, True)
                        if "*" in match.group(0):
                            item["extras"]["access"] = "private"
                        yield item
                elif "IFSC" in location.get() or "Bank" in location.get():  # Bank
                    if "phone" in location_info[0].lower():  # no address or incorrect data
                        continue
                    item = Feature()
                    item["addr_full"] = location_info[0]
                    for info in location_info[1:]:
                        if "phone" in info.lower():
                            item["phone"] = info
                        elif "fax" in info.lower():
                            item["extras"]["fax"] = info
                        elif "hours" in info.lower():
                            item["opening_hours"] = OpeningHours()
                            item["opening_hours"].add_ranges_from_string(info)
                        else:
                            pass  # same IFSC code for many branches, hence not collected
                    if not item.get("phone"):
                        item["addr_full"] = location_info  # only address is present
                    item["ref"] = item["addr_full"]
                    item["website"] = response.url
                    apply_category(Categories.BANK, item)
                    yield item
