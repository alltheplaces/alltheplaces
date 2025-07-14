from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class CryptolinkAUSpider(Spider):
    name = "cryptolink_au"
    item_attributes = {"brand": "Cryptolink", "brand_wikidata": "Q135285381"}
    allowed_domains = ["www.cryptolink.com.au"]
    start_urls = ["https://www.cryptolink.com.au"]

    def parse(self, response: Response) -> Iterable[Request]:
        for location in response.xpath('//div[@class="location-div-block"]'):
            properties = {
                "ref": location.xpath(
                    './div[@class="location-buttons-div-block"]/a[contains(@href, "/locations/cl")]/@href'
                )
                .get()
                .removeprefix("/locations/cl"),
                "located_in": location.xpath("./@data-location-name").get(),
                "lat": location.xpath("./@data-latitude").get(),
                "lon": location.xpath("./@data-longitude").get(),
                "street_address": merge_address_lines(
                    [
                        location.xpath('./div[@class="address-line-1"]/text()').get(),
                        location.xpath('./div[@class="address-line-2"]/text()').get(),
                    ]
                ),
                "city": location.xpath('./div[@class="suburb-state-postcode-line"]/div[1]/text()').get(),
                "state": location.xpath('./div[@class="suburb-state-postcode-line"]/div[2]/text()').get(),
                "postcode": location.xpath('./div[@class="suburb-state-postcode-line"]/div[3]/text()').get(),
                "website": "https://www.cryptolink.com.au"
                + location.xpath(
                    './div[@class="location-buttons-div-block"]/a[contains(@href, "/locations/cl")]/@href'
                ).get(),
                "opening_hours": OpeningHours(),
            }

            apply_category(Categories.ATM, properties)
            properties["extras"]["currency:XBT"] = "yes"
            properties["extras"]["currency:ETH"] = "yes"
            properties["extras"]["currency:USDT"] = "yes"
            properties["extras"]["currency:USDC"] = "yes"
            properties["extras"]["currency:DOGE"] = "yes"
            properties["extras"]["currency:LTC"] = "yes"
            properties["extras"]["currency:ADA"] = "yes"
            properties["extras"]["currency:XRP"] = "yes"
            properties["extras"]["currency:BNB"] = "yes"
            properties["extras"]["currency:TRX"] = "yes"
            properties["extras"]["currency:AUD"] = "yes"

            yield Request(
                url=properties["website"], meta={"item": Feature(**properties)}, callback=self.parse_additional_fields
            )

    def parse_additional_fields(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        apply_yes_no(
            "cash_in",
            item,
            response.xpath('//div[@class="tags-box-location-page"]/div/div[text()="BUY"]/text()').get(),
            False,
        )
        apply_yes_no(
            "cash_out",
            item,
            response.xpath('//div[@class="tags-box-location-page"]/div/div[text()="SELL"]/text()').get(),
            False,
        )
        item["opening_hours"].add_ranges_from_string(
            " ".join(response.xpath('.//div[@class="opening_hours_text_block w-richtext"]//text()').getall())
            .upper()
            .replace("24 H", "00:00 - 23:59 ")
            .replace("24H", "00:00 - 23:59 ")
        )
        item["image"] = response.xpath('//img[@class="location-image"]/@src').get()
        yield item
