from typing import Any

from chompjs import parse_js_object
from scrapy import Selector
from scrapy.http import Request, Response
from scrapy.spiders import CrawlSpider

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class DisChemSpider(CrawlSpider):
    name = "dis_chem"
    item_attributes = {"brand": "Dis-Chem", "brand_wikidata": "Q97274558"}
    allowed_domains = ["dischem.co.za"]
    start_urls = ["https://www.dischem.co.za/stores/"]
    skip_auto_cc_domain = True
    no_refs = True

    def process_results(self, response, results):
        yield from results
        if (
            data_raw := response.xpath('.//script[contains(text(), "var vaimoGtmImpressions = [")]/text()').get()
        ) is not None:
            features_dict = parse_js_object(data_raw.split("var vaimoGtmImpressions =")[1])
            for store in features_dict:
                yield Request(url="https://www.dischem.co.za/" + store["id"], callback=self.parse)

        if (next_url := response.xpath('.//a[@class="action  next"]/@href').get()) is not None:
            yield response.follow(next_url)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["addr_full"] = clean_address(
            response.xpath('.//div[@class="store-detail-block shop-contact-address"]/text()').get().split("Y:")[0]
        )
        item["branch"] = response.xpath('.//h1[@class="page-title store-title"]/span/text()').get()
        item["phone"] = response.xpath('.//div[contains(@class, "phone-number")]/div/span/text()').get()
        item["website"] = response.url
        extract_google_position(item, response)

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
