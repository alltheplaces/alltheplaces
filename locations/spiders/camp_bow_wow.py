from typing import Iterable

from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class CampBowWowSpider(JSONBlobSpider):
    name = "camp_bow_wow"
    item_attributes = {"brand": "Camp Bow Wow", "brand_wikidata": "Q121322343"}
    allowed_domains = ["www.campbowwow.com"]
    start_urls = ["https://www.campbowwow.com/locations/Systems-Advanced-Map.svc?action=GetMapData"]
    locations_key = "Localities"

    def start_requests(self) -> Iterable[Request]:
        for url in self.start_urls:
            yield Request(url=url, headers={"x-request-from": "https://www.campbowwow.com/locations/"})

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Request]:
        item["ref"] = str(feature["ID"])
        item["branch"] = feature["FriendlyName"]
        item.pop("name", None)
        item["street_address"] = merge_address_lines([feature["Address1"], feature["Address2"]])
        item["website"] = "https://www.campbowwow.com" + feature["Path"]
        apply_category(Categories.ANIMAL_BOARDING, item)
        yield Request(url=item["website"], meta={"item": item}, callback=self.parse_opening_hours)

    def parse_opening_hours(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        item["opening_hours"] = OpeningHours()
        hours_text = " ".join(response.xpath('//div[@id="HoursPopup"]//strong[@class="blk"]//text()').getall())
        item["opening_hours"].add_ranges_from_string(hours_text)
        yield item
