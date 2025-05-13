import re
from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.carls_jr_us import CarlsJrUSSpider


class CarlsJrFRSpider(Spider):
    name = "carls_jr_fr"
    item_attributes = CarlsJrUSSpider.item_attributes
    allowed_domains = ["www.carlsjr.fr"]
    start_urls = ["https://www.carlsjr.fr/nos-restaurants"]

    def parse(self, response: Response) -> Iterable[Request]:
        js_file = response.xpath('//script[contains(@src, "front-mainController")]/@src').get()
        yield response.follow(js_file, callback=self.parse_js_file)

    def parse_js_file(self, response: Response) -> Iterable[Request]:
        for store_url in re.findall(r"document\.location\.href[=\s]+\"(.+?)\"", response.text):
            yield response.follow(url=store_url, callback=self.parse_store)

    def parse_store(self, response: Response) -> Iterable[Feature]:
        contact_details = response.xpath('//strong[contains(text(),"Tel:")]/parent::p')
        properties = {
            "ref": response.url,
            "addr_full": merge_address_lines(contact_details.xpath("./strong[1]/text()").getall()),
            "phone": contact_details.xpath('./strong[contains(text(),"Tel:")]/text()')
            .get()
            .strip()
            .removeprefix("Tel: "),
            "website": response.url,
            "opening_hours": OpeningHours(),
        }
        extract_google_position(properties, response)
        hours_text = " ".join(
            response.xpath('//table[contains(@class, "horaires")]/tr/td[position()<=2]/text()').getall()
        )
        properties["opening_hours"].add_ranges_from_string(hours_text, days=DAYS_FR)
        apply_category(Categories.FAST_FOOD, properties)
        yield Feature(**properties)
