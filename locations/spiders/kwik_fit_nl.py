from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature


class KwikFitNLSpider(Spider):
    name = "kwik_fit_nl"
    item_attributes = {"brand": "Kwik Fit", "brand_wikidata": "Q958053"}
    start_urls = ["https://www.kwik-fit.nl/app/depots"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = Feature()
            item["lat"], item["lon"], _, slug, item["street_address"], item["postcode"], item["city"], item["phone"] = (
                location
            )
            item["ref"] = item["website"] = response.urljoin(slug)

            yield item
