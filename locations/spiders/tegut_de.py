import re
from typing import Any
from urllib.parse import urljoin

import scrapy
from scrapy.http import Response

from locations.items import Feature


class TegutDESpider(scrapy.Spider):
    name = "tegut_de"
    item_attributes = {"brand": "tegut", "brand_wikidata": "Q1547993"}
    allowed_domains = ["www.tegut.com"]
    start_urls = [
        "https://www.tegut.com/maerkte/marktsuche.html?mktegut%5Baddress%5D=Stuttgart&mktegut%5Bradius%5D=2000&mktegut%5Bsubmit%5D=Markt+suchen"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for lat, lon, popup in re.findall(
            r"L\.Marker\(\[(-?\d+\.\d+), (-?\d+\.\d+)], {.+?(bindPopup\(\".+?\"\);)", response.text, re.DOTALL
        ):
            # TODO: Decode popup
            item = Feature()
            item["lat"] = lat
            item["lon"] = lon
            item["ref"] = item["website"] = urljoin(
                "https://www.tegut.com/maerkte/markt/",
                re.search(r"([^/]+\.html)", popup).group(1),
            )

            yield item
