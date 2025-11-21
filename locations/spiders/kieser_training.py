import re
from json import loads
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class KieserTrainingSpider(Spider):
    name = "kieser_training"
    item_attributes = {"brand": "Kieser Training", "brand_wikidata": "Q1112367"}

    async def start(self) -> AsyncIterator[Request]:
        for country in ["de", "ch", "at", "lu"]:
            yield Request(url=f"https://www.kieser.com/{country}-en/studios/")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = re.search(
            r"studio_finder = JSON.stringify\((\[.*\])\)",
            response.xpath('//*[contains(text(),"studio_finder = JSON.stringify")]//text()').get(),
        ).group(1)
        for store in loads(raw_data):
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["website"] = "https://www.kieser.com" + store["detail_url"]
            yield Request(url=item["website"], meta={"item": item}, callback=self.parse_details)

    def parse_details(self, response, **kwargs):
        item = response.meta["item"]
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        item["email"] = response.xpath('//*[contains(@href,"mailto:")]/text()').get()
        oh = OpeningHours()
        for day_time in response.xpath(
            '//*[@class="studio-infos__row studio-infos__row--opening-hours"]//*[@class="studio-infos__info"]'
        ):
            oh.add_ranges_from_string(day_time.xpath("normalize-space()").get())
        item["opening_hours"] = oh
        yield item
