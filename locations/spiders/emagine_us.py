from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class EmagineUSSpider(Spider):
    name = "emagine_us"
    item_attributes = {"brand": "Emagine Entertainment", "brand_wikidata": "Q5368794"}
    allowed_domains = ["www.emagine-entertainment.com"]
    custom_settings = {"DOWNLOAD_DELAY": 10}  # Requested by robots.txt

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url="https://www.emagine-entertainment.com/wp-json/emagine/v1/theatres")

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for theatre in response.json()["data"]:
            item = Feature()
            item["ref"] = str(theatre["id"])
            item["name"] = theatre["title"]
            item["street_address"] = theatre["address"]
            item["city"] = theatre["city"]
            item["state"] = theatre["state"]
            item["postcode"] = theatre["postal_code"]
            item["country"] = "US"
            item["lat"] = theatre["latlng"]["latitude"]
            item["lon"] = theatre["latlng"]["longitude"]
            item["website"] = theatre["permalink"]
            item["image"] = theatre.get("featured_image")

            apply_category(Categories.CINEMA, item)

            yield Request(url=item["website"], meta={"item": item}, callback=self.parse_phone)

    def parse_phone(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        # The page also lists a separate automated "Showtimes" hotline; only the
        # "Phone Number" entry is the theatre's own contact number.
        item["phone"] = (
            response.xpath('//h4[normalize-space()="Phone Number"]/following-sibling::p[1]/a/@href')
            .get(default="")
            .removeprefix("tel:")
            or None
        )

        yield item
