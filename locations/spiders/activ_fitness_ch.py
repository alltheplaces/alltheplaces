import json
import re
from typing import Any

from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_DE, DAYS_EN, DAYS_FR, DAYS_IT, OpeningHours
from locations.items import Feature


class ActivFitnessCHSpider(Spider):
    name = "activ_fitness_ch"
    item_attributes = {"brand": "Activ Fitness", "brand_wikidata": "Q123747318"}
    start_urls = ["https://www.activfitness.ch/en/map/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = re.search(
            r"filialfinderData\s*=\s*(\[.*\]);\s* ",
            response.xpath('//*[contains(text(),"filialfinderData")]/text()').get(),
        ).group(1)
        for location in json.loads(raw_data):
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["branch"] = item.pop("name").removeprefix("Activ Fitness ")
            slug = location["url"].split("/")[-2]
            item["extras"]["website:en"] = location["url"]
            item["website"] = item["extras"]["website:de"] = f"https://www.activfitness.ch/studios/{slug}/"
            item["extras"]["website:fr"] = f"https://www.activfitness.ch/fr/studios/{slug}/"
            item["extras"]["website:it"] = f"https://www.activfitness.ch/it/studios/{slug}/"
            yield Request(item["extras"]["website:de"], callback=self.parse_hours_page, cb_kwargs={"item": item})

    def parse_hours_page(self, response: Response, item: Feature) -> Any:
        item["opening_hours"] = self.parse_hours(response.replace(encoding="utf-8"))
        yield item

    days_map = DAYS_DE | DAYS_FR | DAYS_IT | DAYS_EN

    def parse_hours(self, response: Response) -> OpeningHours:
        oh = OpeningHours()
        try:
            rows = response.xpath('//div[contains(@class, "default-opening-times")]//table//tr')
            for row in rows:
                day = row.xpath("td[1]/text()").get("").strip().capitalize()
                hours = row.xpath("td[2]/text()").get("").strip()
                if not day or not hours or hours.lower() in ("geschlossen", "fermé", "chiuso", "closed"):
                    continue
                if "–" in hours:
                    open_time, close_time = hours.split("–")
                    oh.add_range(self.days_map[day], open_time.strip(), close_time.strip())
        except Exception as e:
            self.logger.warning("Failed to parse hours: %s", e)
        return oh
