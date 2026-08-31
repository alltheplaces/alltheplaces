import json
from typing import AsyncIterator, Iterable

from scrapy.http import Request, TextResponse
from scrapy_camoufox.page import PageMethod

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class FleetFarmUSSpider(StructuredDataSpider, CamoufoxSpider):
    name = "fleet_farm_us"
    item_attributes = {"brand": "Fleet Farm", "brand_wikidata": "Q6859973"}
    allowed_domains = ["www.fleetfarm.com"]
    start_urls = ["https://www.fleetfarm.com/sitewide/storeLocator.jsp"]
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS

    async def start(self) -> AsyncIterator[Request]:
        for url in self.start_urls:
            yield Request(
                url,
                callback=self.parse_store_list,
                meta={
                    "camoufox_page_methods": [
                        PageMethod("wait_for_selector", "#storeJsonObjectid", state="attached", timeout=60000)
                    ],
                },
            )

    def parse_store_list(self, response: TextResponse) -> Iterable[Request]:
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
