from scrapy import Selector
from typing import Iterable

from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class YithSpider(JSONBlobSpider):
    """
    Yith
    https://yithemes.com/themes/plugins/yith-store-locator-wordpress/

    To use, specify `allowed_domains`
    """

    locations_key = "markers"
    detection_rules = [
        # DetectionRequestRule(
        #     url=r"^https?:\/\/(?P<allowed_domains__list>[A-Za-z0-9\-.]+)\/wp-admin\/admin-ajax\.php\?action=yith_sl_get_results(.*)$"
        # )
    ]

    def start_requests(self) -> Iterable[Request]:
        yield Request(
            f"https://{self.allowed_domains[0]}/wp-admin/admin-ajax.php?action=yith_sl_get_results&context=frontend&filters[radius][]=500"
        )

    def extract_address(self, item, feature):
        sel = Selector(text=feature["pin_modal"])
        item["addr_full"] = merge_address_lines(sel.xpath('//p[@class="store-address"]/text()').getall())

    def extract_phone(self, item, feature):
        sel = Selector(text=feature["pin_modal"])
        item["phone"] = sel.xpath('//li[@class="store-phone"]/a/text()').get()

    def extract_hours(self, item, feature):
        sel = Selector(text=feature["pin_modal"])
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            " ".join(sel.xpath('//div[@class="store-description"]/p/text()').getall())
        )

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name")
        item["website"] = f"https://{self.allowed_domains[0]}/store-locator/{feature['slug']}/"

        self.extract_address(item, feature)
        self.extract_phone(item, feature)
        self.extract_hours(item, feature)

        yield item
