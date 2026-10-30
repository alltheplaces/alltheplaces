import json
import re
from typing import Iterable

from scrapy import Request
from scrapy.http import Response

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BritHotelFRSpider(StructuredDataSpider):
    name = "brit_hotel_fr"
    item_attributes = {"brand": "Brit Hotel", "brand_wikidata": "Q2925673"}
    start_urls = ["https://www.brithotel.fr/nos-hotels"]
    wanted_types = ["Hotel"]
    search_for_twitter = False
    search_for_facebook = False

    def parse(self, response: Response, **kwargs) -> Iterable[Request]:
        hotels = json.loads(re.search(r"var tab_carte=(\[.+?\]);", response.text).group(1))
        for hotel in hotels:
            url = re.search(r"href='([^'?]+)", hotel["content"]).group(1).strip()
            yield Request(url, callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = re.search(r"var idhotel='(\d+)'", response.text).group(1)
        # Names look like "Brit Hotel Confort Calais" or "Brit Hotel & Spa Colmar East"
        item["branch"] = re.sub(
            r"^Brit\s+(Hotel\s+)?(&\s*(Spa|restaurant)\s+)?((Confort|Essentiel|Privilège)\s+)?",
            "",
            item.pop("name"),
            flags=re.IGNORECASE,
        )
        yield item
