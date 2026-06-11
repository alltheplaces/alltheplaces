import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class SamsChickenGBSpider(Spider):
    name = "sams_chicken_gb"
    item_attributes = {"brand": "Sam's Chicken", "brand_wikidata": "Q24439129"}
    start_urls = ["https://samschicken.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for card in response.xpath('//div[contains(@class, "location-details-container")]'):
            item = Feature()
            item["ref"] = card.xpath("./@onclick").re_first(r"locationClick\((\d+)\)")
            item["branch"] = (
                re.sub(r"^Sam's( Chicken)?", "", card.xpath(".//h5/text()").get("").strip()).lstrip(", ").strip()
            )
            item["street_address"] = " ".join(
                card.xpath('.//span[i[contains(@class, "bi-card-text")]]/text()').get("").split()
            )
            item["postcode"] = " ".join(
                card.xpath('.//span[i[contains(@class, "bi-envelope")]]/text()').get("").split()
            )
            item["phone"] = " ".join(card.xpath('.//span[i[contains(@class, "bi-telephone")]]/text()').get("").split())
            if coords := card.xpath('.//a[contains(@class, "get-direction-a")]/@href').re(
                r"daddr=([\d.\-]+),([\d.\-]+)"
            ):
                item["lat"], item["lon"] = coords

            item["opening_hours"] = OpeningHours()
            for row in card.xpath(".//table//tr"):
                day, open_time, _, close_time = [t.strip() for t in row.xpath("./td//text()").getall() if t.strip()]
                item["opening_hours"].add_range(
                    day,
                    open_time.replace(".", ":").replace(" ", ""),
                    close_time.replace(".", ":").replace(" ", ""),
                    time_format="%I:%M%p",
                )

            apply_category(Categories.FAST_FOOD, item)
            yield item
