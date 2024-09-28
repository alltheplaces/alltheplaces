from scrapy import Spider
from scrapy.http import Request

from locations.google_url import url_to_coords
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingSGSpider(Spider):
    name = "burger_king_sg"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    allowed_domains = ["burgerking.com.sg"]
    website_root = "https://www.burgerking.com.sg"

    def start_requests(self):
        yield from self.request_page(1)

    def request_page(self, page):
        yield Request(url=f"{self.website_root}/Locator?page={page}", callback=self.parse, meta={"page": page})

    def parse(self, response):
        for location in response.xpath('//div[@id="locationsList"]/ul/div'):
            item = Feature()
            item["ref"] = location.xpath("@data-restaurant-id").get()
            item["lat"], item["lon"] = url_to_coords(location.xpath('//a[@class="markerArea"]/@href').get())
            item["branch"] = location.xpath('//dt[@class="mainAddress"]/text()').get().removeprefix("BK ")
            item["phone"] = location.xpath('//span[@class="phone"]/text()').get().replace("Phone:", "")
            item["website"] = f"{self.website_root}/Locator/Details/" + item["ref"]
            yield Request(url=item["website"], callback=self.parse_location, meta={"item": item})
        # if response.xpath('//a[contains(@class, "bk-btn-next")]').get() is not None:
        #     yield from self.request_page(response.meta["page"] + 1)

    def parse_location(self, response):
        item = response.meta["item"]
        item["addr_full"] = clean_address(response.xpath('//span[@itemprop="streetAddress"]/text()').get())

        if (f_hours := response.xpath('string(//div[@class="fh-secondary-list"])').get()) != "":
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                response.xpath('string(//div[@class="fh-secondary-list"])').get()
            )
        elif hours := response.xpath('//*[contains(text(), "Operation Hours")]/text()').get():
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string("Mo-Su " + hours.replace("Operation Hours", ""))

        yield item
