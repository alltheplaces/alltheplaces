from urllib.parse import urljoin

from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class KinkiNLSpider(WPStoreLocatorSpider):
    name = "kinki_nl"
    item_attributes = {"brand": "Kinki Kappers", "brand_wikidata": "Q124152910"}
    allowed_domains = ["www.kinki.nl"]

    def parse_item(self, item: Feature, location: dict, **kwargs):
        item["addr_full"] = None
        item["branch"] = item.pop("name")
        item["website"] = urljoin("https://www.kinki.nl/", location["url"])
        yield item
