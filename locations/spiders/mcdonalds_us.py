from typing import AsyncIterator

from scrapy.http import Request

from locations.geo import country_iseadgg_centroids
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsUSSpider(McdonaldsSpider):
    # Split out of "mcdonalds" because the US grid is large enough that the
    # combined spider hit the run time limit before reaching it.
    name = "mcdonalds_us"

    async def start(self) -> AsyncIterator[Request]:
        template = "https://www.mcdonalds.com/googleappsv2/geolocation?latitude={}&longitude={}&radius=50&maxResults=250&country={}&language={}&showClosed="
        for lat, lon in country_iseadgg_centroids("US", 48):
            yield Request(
                template.format(lat, lon, "us", "en-us"),
                self.parse_major_api,
                cb_kwargs=dict(country="us", locale="en-us"),
            )
