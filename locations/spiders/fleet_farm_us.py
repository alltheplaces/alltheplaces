import json
from typing import Iterable

from scrapy.http import Request, TextResponse

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class FleetFarmUSSpider(StructuredDataSpider):
    name = "fleet_farm_us"
    item_attributes = {"brand": "Fleet Farm", "brand_wikidata": "Q6859973"}
    start_urls = ["https://www.fleetfarm.com/sitewide/storeLocator.jsp"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: TextResponse) -> Iterable[Request]:
        stores = json.loads(response.xpath('//input[@id="storeJsonObjectid"]/@value').get())
        for store in stores:
            # A placeholder/invalid entry (no address, zeroed coordinates) is
            # present in this feed alongside real stores; skip it.
            website = store.get("website")
            if not website or not website.startswith("/visit-stores/"):
                continue
            yield response.follow(website, callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = ld_data["@id"].rsplit("#", 1)[-1]
        apply_category(Categories.SHOP_COUNTRY_STORE, item)
        yield item
