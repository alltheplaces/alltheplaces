from typing import AsyncIterator, Iterable
from urllib.parse import unquote_plus

from scrapy import Selector
from scrapy.http import Request, Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class BedBathNTableSpider(AmastyStoreLocatorSpider):
    name = "bed_bath_n_table"
    item_attributes = {"brand": "Bed Bath N' Table", "brand_wikidata": "Q118551276"}
    domains = [
        "www.bedbathntable.com.au",
        "www.bedbathntable.co.nz",
        "www.bedbathntable.com.sg",
    ]
    data_from_locator_page = {}

    async def start(self) -> AsyncIterator[Request]:
        for domain in self.domains:
            self.data_from_locator_page[domain] = {}
            yield Request(
                url=f"https://{domain}/locator",
                meta={"domain": domain},
                callback=self.scrape_data_from_locator_page,
            )

    async def scrape_data_from_locator_page(self, response: Response) -> AsyncIterator[Request]:
        features_html = response.xpath('//div[@class="amlocator-store-desc"]')
        for feature in features_html:
            ref = feature.xpath(".//@data-amid").get()
            item = Feature()
            item["ref"] = ref
            item["name"] = feature.xpath('.//a[@class="amlocator-link"]/@title').get()
            if "TEMPORARILY CLOSED" in item["name"].upper():
                continue
            item["website"] = feature.xpath('.//a[@class="amlocator-link"]/@href').get()
            item["street_address"] = clean_address(feature.xpath('.//div[@class="store-address"]//text()').getall())
            item["addr_full"] = unquote_plus(
                feature.xpath('.//a[@class="get-direction"]/@href').get().split("//", 2)[2]
            )
            item["phone"] = feature.xpath('.//div[@class="phone"]/text()').get()
            hours_string = " ".join(feature.xpath('.//div[@class="amlocator-schedule-table"]/div/span/text()').getall())
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            self.data_from_locator_page[response.meta["domain"]][ref] = item

        # AmastyStoreLocatorSpider requires exactly one domain in allowed_domains.
        self.allowed_domains = [response.meta["domain"]]
        async for request in super().start():
            yield request

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Feature]:
        if "TEMPORARILY CLOSED" in popup_html.xpath('//a[@class="amlocator-link"]/@title').get("").upper():
            return
        item["ref"] = str(item["ref"])
        for domain in self.domains:
            if domain in item["website"]:
                item.update(self.data_from_locator_page[domain][item["ref"]])
                break
        yield item
