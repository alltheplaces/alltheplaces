from typing import Iterable

from scrapy import Selector

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class PurdysChocolatierCASpider(AmastyStoreLocatorSpider):
    """Purdys Chocolatier store locator spider for Canada. Closes #7271."""

    name = "purdys_chocolatier_ca"
    item_attributes = {
        "brand": "Purdys Chocolatier",
        "brand_wikidata": "Q7261007",
    }
    allowed_domains = ["www.purdys.com"]
    pagination_mode = True
    requires_proxy = True

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Feature]:
        item["ref"] = feature["id"]
        item["branch"] = feature["name"]
        item["country"] = "CA"

        for line in popup_html.xpath('//div[@class="amlocator-info-popup"]/text()').getall():
            line = line.strip()
            if line.startswith("City: "):
                item["city"] = line.removeprefix("City: ").strip()
            elif line.startswith("Postal Code: "):
                item["postcode"] = line.removeprefix("Postal Code: ").strip()
            elif line.startswith("Address: "):
                item["street_address"] = line.removeprefix("Address: ").strip()
            elif line.startswith("State: "):
                item["state"] = line.removeprefix("State: ").strip()

        apply_category(Categories.SHOP_CHOCOLATE, item)
        yield item
