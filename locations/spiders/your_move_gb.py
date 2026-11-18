from typing import Any, Iterable
from urllib.parse import parse_qs, urlparse

from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class YourMoveGBSpider(StructuredDataSpider):
    name = "your_move_gb"
    item_attributes = {"brand": "Your Move", "brand_wikidata": "Q81078416"}
    start_urls = ["https://www.your-move.co.uk/branches"]
    wanted_types = ["RealEstateAgent"]

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        # A single ld+json blob holds an ItemList of RealEstateAgent branches
        for ld_obj in LinkedDataParser.iter_linked_data(response, self.json_parser):
            if ld_obj.get("@type") == "ItemList":
                yield from ld_obj.get("itemListElement", [])

    def post_process_item(self, item, response, ld_data, **kwargs):
        if (item.get("street_address") or "").lower().startswith("c/o"):
            return
        item["branch"] = item.pop("name").removeprefix("Your Move ")
        if image := ld_data.get("image", {}).get("url"):
            item["image"] = image
        item["ref"] = item["website"].split("/")[-1]
        apply_category(Categories.OFFICE_ESTATE_AGENT, item)
        yield Request(item["website"], callback=self.parse_branch, cb_kwargs={"item": item})

    def parse_branch(self, response: Response, item: dict, **kwargs: Any) -> Any:
        if map_url := response.xpath('//@data-srcset[contains(., "staticmap")]').get():
            item["lat"], item["lon"] = parse_qs(urlparse(map_url.split()[0]).query)["center"][0].split(",")
        item["opening_hours"] = OpeningHours()
        for row in response.xpath('//*[@class="opening-time-wrap"]'):
            item["opening_hours"].add_ranges_from_string(" ".join(row.xpath(".//text()").getall()))
        yield item
