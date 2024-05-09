from urllib.parse import unquote_plus

from scrapy import Request

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

    def start_requests(self):
        for allowed_domain in self.allowed_domains:
            self.data_from_locator_page[allowed_domain] = {}
            yield Request(
                url=f"https://{allowed_domain}/locator",
                meta={"allowed_domain": allowed_domain},
                callback=self.scrape_data_from_locator_page,
            )

    def scrape_data_from_locator_page(self, response):
        locations_html = response.xpath('//div[@class="amlocator-store-desc"]')
        for location in locations_html:
            ref = location.xpath(".//@data-amid").get()
            item = Feature()
            item["ref"] = ref
            item["name"] = location.xpath('.//a[@class="amlocator-link"]/@title').get()
            if "TEMPORARILY CLOSED" in item["name"].upper():
                continue
            item["website"] = location.xpath('.//a[@class="amlocator-link"]/@href').get()
            item["street_address"] = clean_address(location.xpath('.//div[@class="store-address"]//text()').getall())
            item["addr_full"] = unquote_plus(
                location.xpath('.//a[@class="get-direction"]/@href').get().split("//", 2)[2]
            )
            item["phone"] = location.xpath('.//div[@class="phone"]/text()').get().strip()
            hours_string = " ".join(
                location.xpath('.//div[@class="amlocator-schedule-table"]/div/span/text()').getall()
            )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            self.data_from_locator_page[response.meta["allowed_domain"]][ref] = item
        yield from super().start_requests()

    def parse_item(self, item, location, popup_html):
        if "TEMPORARILY CLOSED" in popup_html.xpath('//a[@class="amlocator-link"]/@title').get("").upper():
            return
        item["ref"] = str(item["ref"])
        for allowed_domain in self.allowed_domains:
            if allowed_domain in item["website"]:
                item.update(self.data_from_locator_page[allowed_domain][item["ref"]])
                break
        yield item
