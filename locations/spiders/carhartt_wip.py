import re
from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class CarharttWipSpider(Spider):
    name = "carhartt_wip"
    item_attributes = {"brand": "Carhartt Work in Progress", "brand_wikidata": "Q123015694"}
    start_urls = ["https://www.carhartt-wip.com/en-dk/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for slug in re.findall(r"{\\\"href\\\":\\\"/stores/([-\w]+)\\\",", response.text):
            yield Request(
                url=f"https://www.carhartt-wip.com/en-dk/stores/{slug}",
                callback=self.parse_location,
                cb_kwargs=dict(slug=slug),
            )

    def parse_location(self, response: Response, slug: str) -> Any:
        if address := merge_address_lines(response.xpath("//address/p/text()").getall()):
            item = Feature()
            item["ref"] = slug
            item["website"] = response.url
            item["branch"] = response.xpath("//h1/text()").get()
            item["addr_full"] = address
            contact = response.xpath('//div/h2[contains(text(), "Contact")]')
            item["phone"] = contact.xpath("./following-sibling::p[1]/text()").get()
            item["email"] = contact.xpath("./following-sibling::p[2]/text()").get()
            extract_google_position(item, response)
            item["opening_hours"] = OpeningHours()
            for i in range(1, 8):
                day = response.xpath(f"//dt[{i}]/p/text()").get("")
                hours = response.xpath(f"//dd[{i}]/p/text()").get("")
                item["opening_hours"].add_ranges_from_string(f"{day}: {hours}")
            yield item
