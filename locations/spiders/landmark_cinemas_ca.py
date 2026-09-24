import json
from typing import Any, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class LandmarkCinemasCASpider(PlaywrightSpider):
    name = "landmark_cinemas_ca"
    item_attributes = {"brand": "Landmark Cinemas", "brand_wikidata": "Q6484762"}
    start_urls = ["https://www.landmarkcinemas.com/"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Iterable[JsonRequest]:
        for ref in response.xpath('//select[@id="preflocationHomepage"]/option/@value').getall():
            if ref != "-1":
                yield JsonRequest(
                    url=f"https://www.landmarkcinemas.com/umbraco/api/baseapi/GetCinemaInfo?cinemaId={ref}",
                    callback=self.parse_location,
                )

    def parse_location(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        location = json.loads(response.json())
        item = DictParser.parse(location)
        item["branch"] = location["CinemaName"]
        item["website"] = item["ref"] = f'https://www.landmarkcinemas.com{location["CinemaInfoUrl"]}'
        item["image"] = f'https://www.landmarkcinemas.com{location["Image"]}'
        item["street_address"] = merge_address_lines([location["Address1"], location["Address2"]])
        apply_category(Categories.CINEMA, item)

        yield item
