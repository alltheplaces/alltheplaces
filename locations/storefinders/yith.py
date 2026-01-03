from typing import AsyncIterator, Iterable

from scrapy import Selector
from scrapy.http import Request, TextResponse

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class YithSpider(JSONBlobSpider):
    """
    Yith is a self-hosted WordPress plugin storefinder with a website of:
    https://yithemes.com/themes/plugins/yith-store-locator-wordpress/

    To use, specify `allowed_domains` as a list containing a single domain
    name only.
    """

    allowed_domains: list[str] = []
    locations_key: str | list[str] = "markers"
    # detection_rules = [
    #    DetectionRequestRule(
    #        url=r"^https?:\/\/(?P<allowed_domains__list>[A-Za-z0-9\-.]+)\/wp-admin\/admin-ajax\.php\?action=yith_sl_get_results(.*)$"
    #    )
    # ]

    async def start(self) -> AsyncIterator[Request]:
        if len(self.allowed_domains) != 1:
            raise ValueError("Specify one domain name in the allowed_domains list attribute.")
            return
        yield Request(
            f"https://{self.allowed_domains[0]}/wp-admin/admin-ajax.php?action=yith_sl_get_results&context=frontend&filters[radius][]=500"
        )

    def extract_address(self, item: Feature, feature: dict) -> None:
        sel = Selector(text=feature["pin_modal"])
        item["addr_full"] = merge_address_lines(sel.xpath('//p[@class="store-address"]/text()').getall())

    def extract_phone(self, item: Feature, feature: dict) -> None:
        sel = Selector(text=feature["pin_modal"])
        item["phone"] = sel.xpath('//li[@class="store-phone"]/a/text()').get()

    def extract_hours(self, item: Feature, feature: dict) -> None:
        sel = Selector(text=feature["pin_modal"])
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            " ".join(sel.xpath('//div[@class="store-description"]/p/text()').getall())
        )

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = f"https://{self.allowed_domains[0]}/store-locator/{feature['slug']}/"

        self.extract_address(item, feature)
        self.extract_phone(item, feature)
        self.extract_hours(item, feature)

        yield item
