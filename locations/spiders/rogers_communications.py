import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class RogersCommunicationsSpider(SitemapSpider):
    name = "rogers_communications"
    item_attributes = {"brand": "Rogers", "brand_wikidata": "Q3439663"}
    allowed_domains = ["rogers.com"]
    sitemap_urls = ["https://www.rogers.com/stores/sitemap.xml"]
    sitemap_rules = [(r"^https://www\.rogers\.com/stores/(?!fr_ca/)(?!index\.html)[^/]+(?:/[^/]+)?$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if not response.xpath('//main[@itemtype="http://schema.org/MobilePhoneStore"]'):
            return

        item = Feature()
        item["ref"] = item["website"] = response.url

        if m := re.search(r"Rogers Store at\s+(.*?)\s*-\s", response.xpath("//title/text()").get() or ""):
            if branch := m.group(1).strip():
                item["branch"] = branch

        item["street_address"] = merge_address_lines(
            [
                response.xpath('//span[@class="c-address-street-1"]/text()').get(),
                response.xpath('//span[@class="c-address-street-2"]/text()').get(),
            ]
        )
        item["city"] = response.xpath('//span[@class="c-address-city"]/text()').get()
        item["state"] = response.xpath('//abbr[contains(@class,"c-address-state")]/text()').get()
        item["postcode"] = response.xpath('//*[@itemprop="postalCode"]/text()').get()
        item["lat"] = response.xpath('//meta[@itemprop="latitude"]/@content').get()
        item["lon"] = response.xpath('//meta[@itemprop="longitude"]/@content').get()
        item["phone"] = response.xpath('//*[@itemprop="telephone"]/text()').get()

        if data_days := response.xpath('//*[contains(@class,"js-hours-table")]/@data-days').get():
            item["opening_hours"] = self.parse_hours(data_days)

        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item

    @staticmethod
    def parse_hours(data_days: str) -> OpeningHours:
        oh = OpeningHours()
        for day in json.loads(data_days):
            if day.get("isClosed"):
                continue
            for interval in day.get("intervals") or []:
                oh.add_range(
                    day=day["day"].title()[:2],
                    open_time=str(interval["start"]).zfill(4),
                    close_time=str(interval["end"]).zfill(4),
                    time_format="%H%M",
                )
        return oh
