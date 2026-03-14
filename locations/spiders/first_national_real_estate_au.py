from scrapy import Spider

from locations.categories import Categories
from locations.google_url import extract_google_position
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
            href = location.xpath('.//a[contains(@class, "office-name")]/@href').get()
            phone = location.xpath('.//a[contains(@href, "tel:")]/@href').get()
            email = location.xpath('.//a[contains(@href, "mailto:")]/@href').get()

            item = Feature(
                ref=href.split("/office/", 1)[1].split("/", 1)[0] if href else None,
                branch=location.xpath('.//a[contains(@class, "office-name")]/text()')
                .get(default="")
                .removeprefix("First National Real Estate ")
                .strip()
                or None,
                addr_full=clean_address(location.xpath('.//div[contains(@class, "office-address")]//text()').getall()),
                website=f"https://www.firstnational.com.au{href.strip()}" if href else None,
                phone=phone.replace("tel:", "") if phone else None,
                email=email.replace("mailto:", "") if email else None,
            )
            extract_google_position(item, location)
            yield item
