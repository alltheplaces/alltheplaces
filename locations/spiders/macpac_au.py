from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class MacpacAUSpider(Spider):
    name = "macpac_au"
    item_attributes = {"brand": "Macpac", "brand_wikidata": "Q6724943"}
    allowed_domains = ["www.macpac.com.au"]
    start_urls = [
        "https://www.macpac.com.au/our-stores/submit?dwfrm_storelocator_findbycountry=search&format=ajax&dwfrm_storelocator_country=AU"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store_id in response.xpath("//@data-storeid").getall():
            yield response.follow(f"/our-stores/details?StoreID={store_id}&format=ajax", self.parse_store)

    def parse_store(self, response: Response) -> Iterable[Feature]:
        name = response.xpath('normalize-space(//div[@class="store-name small-10 cell"])').get()
        if name.upper().startswith("OPENING SOON"):
            return

        item = Feature()
        item["ref"] = response.xpath('//*[@id="set-preferred-store"]/@data-id').get()
        item["branch"] = name.removeprefix("Macpac ")
        item["lat"] = response.xpath('//div[@class="additional-info"]/@data-lat').get()
        item["lon"] = response.xpath('//div[@class="additional-info"]/@data-lng').get()
        item["phone"] = response.xpath('//a[starts-with(@href, "tel:")]/@href').get("")
        item["website"] = "https://www.macpac.com.au/our-stores"

        address_lines = [
            line.strip()
            for line in response.xpath('//div[@class="store-details"]/div[@class="main-info"][1]/text()').getall()
            if line.strip()
        ]
        if len(address_lines) >= 2:
            item["postcode"] = address_lines.pop()
            item["city"] = address_lines.pop()
        item["street_address"] = merge_address_lines(address_lines)

        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            " ".join(response.xpath('//div[@class="store-hours"]/text()').getall())
        )

        apply_category(Categories.SHOP_OUTDOOR, item)
        yield item
