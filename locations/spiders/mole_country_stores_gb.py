import re
from typing import Any

from requests import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class MoleCountryStoresGBSpider(CrawlSpider):
    name = "mole_country_stores_gb"
    item_attributes = {"brand": "Mole Valley Farmers", "brand_wikidata": "Q6895915"}
    start_urls = ["https://www.moleonline.com/storelocator/directory/"]
    rules = [Rule(LinkExtractor(allow=r"/storelocator/index/store/\d+/"), callback="parse_store")]

    def parse_store(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = response.url.split("/")[-2]
        item["branch"] = item["ref"].replace("-", " ").title()
        item["name"] = "Mole Country Stores"
        item["phone"] = response.xpath('//li[contains(@class, "iweb-sl-store-phone")]//a/text()').get()
        item["website"] = response.url
        if address_lines := response.xpath('//address[contains(@class, "iweb-sl-store-address")]/text()').getall():
            if any(name in address_lines[0] for name in ("Mole Country Stores", "Mole Valley Farmers")):
                address_lines = address_lines[1:]
            item["addr_full"] = merge_address_lines(address_lines)

        item["opening_hours"] = self.parse_hours(response)
        extract_google_position(item, response)
        apply_category(Categories.SHOP_COUNTRY_STORE, item)

        yield item

    @staticmethod
    def parse_hours(response: Response) -> OpeningHours:
        oh = OpeningHours()
        for row in response.xpath('//table[contains(@class, "store-view__hours")]//tr'):
            day = row.xpath("./th/text()").get()
            time_text = "".join(row.xpath("./td//text()").getall()).strip()
            if not day or not time_text or "Closed" in time_text:
                continue
            times = re.compile(r"\s*[–-]\s*").split(time_text)
            if len(times) == 2:
                oh.add_range(day.strip(), *times)
        return oh
