from typing import Iterable
from urllib.parse import urljoin

from scrapy.http import Response

from locations.hours import DAYS_NL
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class KinkiNLSpider(WPStoreLocatorSpider):
    name = "kinki_nl"
    item_attributes = {"brand": "Kinki Kappers", "brand_wikidata": "Q124152910"}
    allowed_domains = ["www.kinki.nl"]
    days = DAYS_NL

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["addr_full"] = None
        item["branch"] = item.pop("name")
        item["website"] = urljoin("https://www.kinki.nl/", feature["url"])
        yield item
