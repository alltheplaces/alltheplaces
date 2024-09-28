from scrapy import Spider
from scrapy.http import Request
from scrapy.linkextractors import LinkExtractor

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingMYSpider(Spider):
    name = "burger_king_my"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    allowed_domains = ["burgerking.com.my"]

    def start_requests(self):
        yield from self.request_page(1)

    def request_page(self, page):
        yield Request(url=f"https://burgerking.com.my/Locator?page={page}", callback=self.parse, meta={"page": page})

    def parse(self, response):
        for link in LinkExtractor(allow="/Locator/Details/").extract_links(response):
            yield Request(url=link.url, callback=self.parse_location)
        if response.xpath('//a[contains(@class, "bk-btn-next")]').get() is not None:
            yield from self.request_page(response.meta["page"] + 1)

    def parse_location(self, response):
        item = Feature()
        item["ref"] = response.url.replace("https://burgerking.com.my/Locator/Details/", "")
        item["website"] = response.url
        extract_google_position(item, response)
        item["branch"] = (
            response.xpath('//span[@itemtype="http://schema.org/PostalAddress"]/span/text()').get().replace("BK ", "")
        )
        item["addr_full"] = clean_address(response.xpath('//span[@itemprop="streetAddress"]/text()').get())

        if hours := response.xpath('//*[contains(text(), "Operation Hours")]/text()').get():
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string("Mo-Su " + hours.replace("Operation Hours", ""))

        yield item
