from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class EmiratesPostAESpider(Spider):
    """
    Emirates Post's own locator (www.emiratespost.ae) sits behind a Cloudflare managed
    challenge, so this uses the "Emirates post offices GIS location" dataset that Emirates
    Post Group publishes on the UAE federal open data portal (bayanat.ae):
    https://bayanat.ae/en/Datasets/Dataset-info?id=meRyywoUonQVlTP2DqqkgYVQ-dSCQKJt6lCB-42SVUI
    The dataset was last updated in 2018.
    """

    name = "emirates_post_ae"
    item_attributes = {"operator": "Emirates Post", "operator_wikidata": "Q5372577"}
    allowed_domains = ["bayanat.ae"]
    # bayanat.ae/robots.txt asks for "Crawl-delay: 10"; this is a single request anyway.
    custom_settings = {"DOWNLOAD_DELAY": 10}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            "https://bayanat.ae/api/DatasetResources/GetDatasetResource?resourceID=a04ad462-8efa-4699-9e01-9fadca3a2f8d"
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for row in response.json():
            # Some column names carry a trailing space ("Emirates "), so normalise the keys.
            row = {key.strip(): (value or "").strip() for key, value in row.items()}
            item = Feature()
            item["ref"] = row["Code"]
            item["name"] = row["Branch postoffice name"]
            item["extras"] = {"name:en": row["Branch postoffice name"], "name:ar": row["Branch postoffice name_AR"]}
            item["lat"] = row["updated Latitude"]
            item["lon"] = row["updated Longitude"]
            # "Emirates" holds the emirate, except that Al Ain (a city in Abu Dhabi emirate) is listed separately.
            if row["Emirates"] == "Al Ain":
                item["city"] = "Al Ain"
                item["state"] = "Abu Dhabi"
            else:
                item["state"] = row["Emirates"]
            apply_category(Categories.POST_OFFICE, item)
            yield item
