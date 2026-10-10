import re
from typing import Any, Iterable

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class DelFriscosGrilleUSSpider(StructuredDataSpider):
    name = "del_friscos_grille_us"
    item_attributes = {"brand": "Del Frisco's Grille"}
    allowed_domains = ["www.delfriscosgrille.com"]
    start_urls = ["https://www.delfriscosgrille.com/view-all-locations/"]
    wanted_types = ["FoodEstablishment"]

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        for ld_obj in LinkedDataParser.iter_linked_data(response, self.json_parser):
            yield from ld_obj.get("subOrganization", [])

    def post_process_item(self, item, response, ld_data, **kwargs) -> Any:
        branch = item.pop("name")
        item["name"] = "Del Frisco's Grille"
        item["branch"] = re.sub(r",\s*[A-Z]{2}$", "", branch)
        item["ref"] = item["website"].rstrip("/").rsplit("/", 1)[-1]
        item["extras"]["cuisine"] = "american"
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
        opening_hours = OpeningHours()
        for line in response.xpath('//section[@id="intro"]//p/text()').getall():
            line = line.strip()
            if re.match(
                r"^[A-Z]{3}(?:\s*-\s*[A-Z]{3})?:\s*\d{1,2}:\d{2} [AP]M - \d{1,2}:\d{2} [AP]M$",
                line,
            ):
                opening_hours.add_ranges_from_string(line)

        return opening_hours if opening_hours.as_opening_hours() else None
