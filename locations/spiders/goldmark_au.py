from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories
from locations.google_url import url_to_coords
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class GoldmarkAUSpider(Spider):
    name = "goldmark_au"
    item_attributes = {"brand": "Goldmark", "brand_wikidata": "Q17005474", "extras": Categories.SHOP_JEWELRY.value}
    allowed_domains = ["www.goldmark.com.au"]
    start_urls = ["https://www.goldmark.com.au/stores/all-stores"]

    def parse(self, response: Response) -> Iterable[Feature]:
        for feature in response.xpath('//div[contains(@class, "stores-grid--store")]'):
            properties = {
                "ref": feature.xpath('./div[contains(@class, "store-details-wrapper")]/a/@data-storeid').get(),
                "branch": feature.xpath('./div[contains(@class, "store-details-wrapper")]/a/text()').get("").strip().removeprefix("Goldmark AU ").removeprefix("Goldmark NZ ").split("(", 1)[0],
                "addr_full": clean_address(feature.xpath('./div[contains(@class, "store-details-wrapper")]/p[last()]/text()').getall()).removesuffix("Phone:"),
                "phone": feature.xpath('./div[contains(@class, "store-details-wrapper")]/p[last()]/a[contains(@href, "tel:")]/@href').get().removeprefix("tel:"),
                "opening_hours": OpeningHours(),
            }
            properties["lat"], properties["lon"] = url_to_coords(feature.xpath('./div[contains(@class, "store-directions-wrapper")]/a/@href').get())

            hours_text = " ".join(filter(None, map(str.strip, feature.xpath('./div[contains(@class, "store-hours-wrapper")]//text()').getall())))
            properties["opening_hours"].add_ranges_from_string(hours_text)

            yield Feature(**properties)
