from json import loads
from typing import Iterable

from scrapy import Selector
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class LcboCASpider(AmastyStoreLocatorSpider):
    name = "lcbo_ca"
    item_attributes = {"brand": "LCBO", "brand_wikidata": "Q845263"}
    allowed_domains = ["www.lcbo.com"]
    pagination_mode = True
    custom_settings = {
        "ROBOTSTXT_OBEY": False
    }  # robots.txt has a blocking rule for any URL with a query component ("?attrib=value")

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Request]:
        item["ref"] = popup_html.xpath(".//@data-storeidentifier").get()
        item["branch"] = popup_html.xpath(".//@data-storename").get()
        item["postcode"] = (
            popup_html.xpath('(.//div[@class="amlocator-info-popup"]/text())[2]').get("").strip(", ").split(" ", 1)[1]
        )
        item["state"] = (
            popup_html.xpath('(.//div[@class="amlocator-info-popup"]/text())[2]').get("").strip(", ").split(" ", 1)[0]
        )
        item["addr_full"] = merge_address_lines(
            [
                popup_html.xpath('.//span[@class="amlocator-info-address"]/text()').get(),
                item.get("state"),
                item.get("postcode"),
            ]
        )
        item["website"] = popup_html.xpath('.//a[@class="amlocator-link-store-details"]/@href').get()
        item["phone"] = (
            popup_html.xpath('.//a[@class="amlocator-phone-number"]/@href').get("").replace("tel:", "").strip("[]")
        )
        apply_category(Categories.SHOP_ALCOHOL, item)
        item["extras"]["alt_ref"] = str(feature["id"])
        yield Request(
            url="https://www.lcbo.com/en/storepickup/selection/store/?value={}&st_loc_flag=true".format(item["ref"]),
            meta={"item": item},
            headers={"X-Requested-With": "XMLHttpRequest"},
            callback=self.parse_additional_attributes,
        )

    def parse_additional_attributes(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]

        if not response.json()["success"]:
            # Store ID may not exist anymore, or may be a new store, and there
            # is a mismatch between store data in the Amasty and store pickup
            # selection APIs.
            # At 2025-05-28, only 3 of 688 responses reached this code branch.
            yield item
            return

        feature = response.json()["output"]
        item["street_address"] = feature["address"]
        item["city"] = feature["city"]

        item["opening_hours"] = OpeningHours()
        for day_name, day_hours in loads(feature["schedule"]).items():
            if day_hours[f"{day_name}_status"] != "1":
                item["opening_hours"].set_closed(DAYS_EN[day_name.title()])
            else:
                day_start = day_hours["from"]["hours"] + ":" + day_hours["from"]["minutes"]
                day_end = day_hours["to"]["hours"] + ":" + day_hours["to"]["minutes"]
                break_start = day_hours["break_from"]["hours"] + ":" + day_hours["break_from"]["minutes"]
                break_end = day_hours["break_to"]["hours"] + ":" + day_hours["break_to"]["minutes"]
                if break_start == "00:00" and break_end == "00:00":
                    # No break in the day.
                    item["opening_hours"].add_range(DAYS_EN[day_name.title()], day_start, day_end)
                else:
                    # Day has a break in the middle.
                    item["opening_hours"].add_range(DAYS_EN[day_name.title()], day_start, break_start)
                    item["opening_hours"].add_range(DAYS_EN[day_name.title()], break_end, day_end)

        yield item
