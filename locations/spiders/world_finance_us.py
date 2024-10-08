from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class WorldFinanceUSSpider(Spider):
    name = "world_finance_us"
    item_attributes = {"brand": "World Finance", "brand_wikidata": "Q3569971"}
    start_urls = ["https://www.loansbyworld.com/find-a-branch"]

    def parse(self, response: Response) -> Any:
        for location in response.xpath('//div[@class="branch-data"]'):
            properties = {
                "ref": location.xpath(".//@data-branch-id").get(),
                "lat": location.xpath(".//@data-branch-lat").get(),
                "lon": location.xpath(".//@data-branch-lng").get(),
                "addr_full": location.xpath(".//@data-branch-address").get(),
                "street_address": clean_address(
                    [location.xpath(".//@data-branch-line1").get(), location.xpath(".//@data-branch-line2").get()]
                ),
                "city": location.xpath(".//@data-branch-city").get(),
                "state": location.xpath(".//@data-branch-state").get(),
                "postcode": location.xpath(".//@data-branch-zip").get(),
                "phone": location.xpath(".//@data-branch-phone").get(),
                "website": "https://www.loansbyworld.com/branches/branch-" + location.xpath(".//@data-branch-id").get(),
            }
            yield Request(
                url=properties["website"], callback=self.parse_opening_hours, meta={"item": Feature(**properties)}
            )

    def parse_opening_hours(self, response: Response) -> Any:
        item = response.meta["item"]
        hours_string = " ".join(
            filter(None, map(str.strip, response.xpath('//div[@class="dates_list"]//text()').getall()))
        )
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
