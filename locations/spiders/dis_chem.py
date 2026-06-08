import re
from typing import Any

from scrapy import Selector
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class DisChemSpider(Spider):
    name = "dis_chem"
    item_attributes = {"brand": "Dis-Chem", "brand_wikidata": "Q97274558"}
    allowed_domains = ["dischem.co.za"]
    start_urls = ["https://www.dischem.co.za/find-a-store"]
    skip_auto_cc_domain = True
    no_refs = True
    requires_proxy = "ZA"

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for link in response.xpath('.//a[@class="product-item-link"]/@href').getall():
            yield response.follow(link, callback=self.parse_store)

        if (next_url := response.xpath('.//a[@class="action  next"]/@href').get()) is not None:
            yield response.follow(next_url)

    def parse_store(self, response: Response, **kwargs: Any) -> Any:
        if (title := response.xpath('.//h1[contains(@class, "page-title")]/span/text()').get()) is None:
            return
        if "search results" in title.lower():
            return
        item = Feature()
        if addr_raw := response.xpath('.//div[@class="store-detail-block shop-contact-address"]/text()').get():
            item["addr_full"] = clean_address(addr_raw.split("Y:")[0])
        item["branch"] = response.xpath('.//h1[contains(@class, "store-title")]/span/text()').get()
        item["phone"] = response.xpath('.//div[contains(@class, "phone-number")]/div/span/text()').get()
        item["website"] = response.url

        for script in response.xpath(".//script/text()").getall():
            if "initMap" in script:
                if (lat_match := re.search(r"lat:\s*([-\d.]+)", script)) and (
                    lng_match := re.search(r"lng:\s*([-\d.]+)", script)
                ):
                    item["lat"] = float(lat_match.group(1))
                    item["lon"] = float(lng_match.group(1))
                break

        item["opening_hours"] = OpeningHours()
        # First opening hours results are for the store, others may be for other departments
        for day in response.xpath(
            './/div[contains(@class, "shop-services-opening-times")]//span[contains(@class, "day-name")]'
        ).getall()[0:7]:
            day_hours = Selector(text=day).xpath("string(.)").get().strip()
            if "closed" in day_hours.lower():
                item["opening_hours"].set_closed(day_hours.split(" ")[0])
            else:
                item["opening_hours"].add_ranges_from_string(day_hours)

        yield item
