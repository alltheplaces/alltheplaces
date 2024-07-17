import html
from typing import Any

import scrapy
from scrapy.http import Response

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class AnytimeFitnessSpider(scrapy.Spider):
    name = "anytime_fitness"
    item_attributes = {"brand": "Anytime Fitness", "brand_wikidata": "Q4778364"}
    start_urls = ["https://www.anytimefitness.com/wp-content/uploads/locations.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for gym in response.json():
            yield Feature(
                lat=gym["latitude"],
                lon=gym["longitude"],
                street_address=clean_address([gym["content"]["address"], gym["content"]["address2"]]),
                city=gym["content"]["city"],
                phone=gym["content"]["phone"],
                website=gym["content"]["url"].replace(
                    "https://anytimefitness.co.uk", "https://www.anytimefitness.co.uk"
                ),
                email=gym["content"]["email"],
                state=gym["content"]["state_abbr"],
                postcode=gym["content"]["zip"],
                ref=gym["content"]["number"],
                country=gym["content"]["country"],
                branch=html.unescape(gym["content"]["title"]),
            )
