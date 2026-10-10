import re
from typing import Any, Iterable

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class JoesCrabShackUSSpider(StructuredDataSpider):
    name = "joes_crab_shack_us"
    item_attributes = {"brand": "Joe's Crab Shack", "brand_wikidata": "Q6208210"}
    allowed_domains = ["www.joescrabshack.com"]
    start_urls = ["https://www.joescrabshack.com/view-all-locations/"]
    wanted_types = ["FoodEstablishment"]

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        for ld_obj in LinkedDataParser.iter_linked_data(response, self.json_parser):
            yield from ld_obj.get("subOrganization", [])

    def post_process_item(self, item, response, ld_data, **kwargs) -> Any:
        item["branch"] = re.sub(r",\s*[A-Z]{2}$", "", item.pop("name"))
        item["ref"] = item["website"].rstrip("/").rsplit("/", 1)[-1]
        item["extras"]["cuisine"] = "seafood"
        apply_category(Categories.RESTAURANT, item)

        yield Request(url=item["website"], callback=self.parse_location, meta={"item": item})

    def parse_location(self, response: Response, **kwargs: Any) -> Iterable[dict]:
        item = response.meta["item"]
        item["lat"] = response.xpath('//div[contains(@class, "gmaps")]/@data-gmaps-lat').get()
        item["lon"] = response.xpath('//div[contains(@class, "gmaps")]/@data-gmaps-lng').get()
        item["opening_hours"] = self.parse_opening_hours(response)
        yield item

    @staticmethod
    def parse_opening_hours(response: Response) -> OpeningHours | None:
        hours_string = " ".join(
            line.strip()
            for line in response.xpath('//section[@id="intro"]//p/text()[contains(., ":")]').getall()
            if line.strip()
        )

        if not hours_string:
            return None

        opening_hours = OpeningHours()
        opening_hours.add_ranges_from_string(hours_string)
        return opening_hours if opening_hours.as_opening_hours() else None
