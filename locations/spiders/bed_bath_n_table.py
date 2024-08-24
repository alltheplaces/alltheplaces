from typing import Iterable
from urllib.parse import unquote_plus

from scrapy import Request, Selector
from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class BedBathNTableSpider(AmastyStoreLocatorSpider):
    name = "bed_bath_n_table"
    item_attributes = {"brand": "Bed Bath N' Table", "brand_wikidata": "Q118551276"}
    allowed_domains = [
        "www.bedbathntable.com.au",
        "www.bedbathntable.co.nz",
        "www.bedbathntable.com.sg",
    ]
    data_from_locator_page = {}

    def start_requests(self) -> Iterable[Request]:
        for allowed_domain in self.allowed_domains:
            self.data_from_locator_page[allowed_domain] = {}
            yield Request(
                url=f"https://{allowed_domain}/locator",
                meta={"allowed_domain": allowed_domain},
                callback=self.scrape_data_from_locator_page,
            )

    def scrape_data_from_locator_page(self, response: Response) -> Iterable[Request]:
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
            item["phone"] = feature.xpath('.//div[@class="phone"]/text()').get().strip()
            hours_string = " ".join(feature.xpath('.//div[@class="amlocator-schedule-table"]/div/span/text()').getall())
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            self.data_from_locator_page[response.meta["allowed_domain"]][ref] = item
        yield from super().start_requests()

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Feature]:
        if "TEMPORARILY CLOSED" in popup_html.xpath('//a[@class="amlocator-link"]/@title').get("").upper():
            return
        item["ref"] = str(item["ref"])
        for allowed_domain in self.allowed_domains:
            if allowed_domain in item["website"]:
                item.update(self.data_from_locator_page[allowed_domain][item["ref"]])
                break
        yield item
