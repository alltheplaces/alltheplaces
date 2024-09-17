from scrapy import Spider

from locations.categories import Categories
from locations.google_url import url_to_coords
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class FirstNationalRealEstateAUSpider(Spider):
    name = "first_national_real_estate_au"
    item_attributes = {
        "brand": "First National Real Estate",
        "brand_wikidata": "Q122888198",
        "extras": Categories.OFFICE_ESTATE_AGENT.value,
    }
    allowed_domains = ["www.firstnational.com.au"]
    start_urls = ["https://www.firstnational.com.au/pages/real-estate/offices"]

    def parse(self, response):
        for location in response.xpath('//ul[contains(@class, "office-listing")]/li[@class="office-list"]'):
            properties = {
                "ref": location.xpath('.//a[contains(@class, "office-name")]/@href')
                .get()
                .split("/office/", 1)[1]
                .split("/", 1)[0],
                "branch": location.xpath('.//a[contains(@class, "office-name")]/text()')
                .get()
                .removeprefix("First National Real Estate ")
                .strip(),
                "addr_full": clean_address(
                    location.xpath('.//div[contains(@class, "office-address")]//text()').getall()
                ),
                "website": "https://www.firstnational.com.au"
                + location.xpath('.//a[contains(@class, "office-name")]/@href').get().strip(),
                "phone": location.xpath('.//a[contains(@href, "tel:")]/@href').get().replace("tel:", "").strip(),
                "email": location.xpath('.//a[contains(@href, "mailto:")]/@href').get().replace("mailto:", "").strip(),
            }
            properties["lat"], properties["lon"] = url_to_coords(
                location.xpath('.//img[@class="office-map"]/@src').get()
            )
            yield Feature(**properties)
