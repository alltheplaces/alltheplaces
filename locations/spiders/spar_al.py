from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature
from locations.spiders.spar_aspiag import SPAR_SHARED_ATTRIBUTES


class SparALSpider(Spider):
    name = "spar_al"
    item_attributes = SPAR_SHARED_ATTRIBUTES
    start_urls = ["https://www.spar.al/index.php/en/spar-map"]
    no_refs = True

    def parse(self, response: Response) -> Iterable[Feature]:
        for location in response.xpath('//select[@id="toPMAddressPlgPM1"]/option'):
            item = Feature()
            item["lat"], item["lon"] = location.xpath("@value").get().split(",")[:2]
            # location.xpath("/text()") # branch? address
            yield item
