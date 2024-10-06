from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser


class SostreneGreneSpider(Spider):
    name = "sostrene_grene"
    item_attributes = {"brand": "Søstrene Grene", "brand_wikidata": "Q10730152"}

    def start_requests(self) -> Iterable[Request]:
        for lang in ["da-DK", "fr-FR", "nl-NL", "de-AT", "de-DE", "en-IE", "en-GB", "nb-NO", "sv-SE", "en-FI"]:
            yield JsonRequest(
                url="https://sostrenegrene.com/umbraco/api/store/search", headers={"culture": lang}, dont_filter=True
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["stores"]:
            item = DictParser.parse(location["store"])
            item["branch"] = item.pop("name")
            item["website"] = response.urljoin(item["website"])

            yield item
