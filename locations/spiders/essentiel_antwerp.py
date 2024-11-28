from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class EssentielAntwerpSpider(CrawlSpider):
    name = "essentiel_antwerp"
    item_attributes = {"brand": "Essentiel Antwerp", "brand_wikidata": "Q117456339"}
    start_urls = ["https://www.essentiel-antwerp.com/be_en/ourstores"]

    rules = [
        Rule(
            LinkExtractor(
                restrict_xpaths='//*[@class="sps-NpIex BuilderAccordion_accordion_item__pPRwV"]//*[@class="sps-C92Xj"]//a'
            ),
            callback="parse",
        )
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["street_address"] = response.xpath("//p/text()").get()
        item["addr_full"] = merge_address_lines(
            [item["street_address"], response.xpath("//p[2]/text()").get(), response.xpath("//p[3]/text()").get()]
        )
        item["website"] = item["ref"] = response.url
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]//text()').get()
        extract_google_position(item, response)
        item["opening_hours"] = OpeningHours()
        for time_string in response.xpath('(//*[@class="ImageBlock_paragraph__43zjD"])[3]//p'):
            time = time_string.xpath(".//text()").get()
            if time in ["Closed", None]:
                continue
            if "&" in time:
                for open_close_time in time.split("&"):
                    open_time, close_time = open_close_time.split("-")
            else:
                open_time, close_time = time.split("—")
            for day in DAYS_FULL:
                item["opening_hours"].add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip())
        yield item
