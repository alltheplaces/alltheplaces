import re
from html import unescape
from typing import Iterable

from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_AT, DAYS_AT, OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class BellafloraATSpider(Spider):
    name = "bellaflora_at"
    item_attributes = {"brand": "Bellaflora", "brand_wikidata": "Q815787"}
    allowed_domains = ["www.bellaflora.at"]
    start_urls = ["https://www.bellaflora.at/filialfinder"]
    user_agent = BROWSER_DEFAULT

    def start_requests(self) -> Iterable[FormRequest]:
        headers = {
            "X-Requested-With": "XMLHttpRequest",
        }
        formdata = {
            "ChainStoreList.Method2": "Body",
            "ChainStoreList.Mode": "List",
            "ChainStoreList.PageIndex": "0",
            "ChainStoreList.PageSize": "5000",
            "ChainStoreList.LocationByIP": "true",
            "Instance": "ChainStoreList",
        }
        yield FormRequest(url=self.start_urls[0], headers=headers, formdata=formdata, method="POST")

    def parse(self, response: Response) -> Iterable[Feature]:
        for location in response.xpath('.//div[contains(@id, "ChainStore_")]'):
            properties = {
                "ref": location.xpath("./@id").get().split("_", 1)[1],
                "name": unescape(location.xpath("./@name").get()),
                "lat": location.xpath("./@latitude").get(),
                "lon": location.xpath("./@longitude").get(),
                "addr_full": location.xpath('.//div[@class="store-address"]/span/text()').get(),
                "opening_hours": OpeningHours(),
            }

            if phone_uri := location.xpath('.//div[@class="phone-info"]//a[contains(@href, "tel:")]/@href').get():
                properties["phone"] = phone_uri.removeprefix("tel:")

            if website_link := location.xpath('.//div[@class="button-area"]/a/@href').get():
                properties["website"] = f"https://www.bellaflora.at{website_link}"

            hours_string = re.sub(
                r"\s+",
                " ",
                " ".join(
                    location.xpath(
                        './/div[@class="openingtime-item"]/div[contains(@class, "dateTimeWrapper")]//text()'
                    ).getall()
                ),
            )
            properties["opening_hours"].add_ranges_from_string(hours_string, days=DAYS_AT, closed=CLOSED_AT)

            apply_category(Categories.SHOP_GARDEN_CENTRE, properties)

            yield Feature(**properties)
