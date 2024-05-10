from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories
from locations.google_url import extract_google_position
from locations.hours import DAYS_NL, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class PhoneHouseNLSpider(CrawlSpider):
    name = "phone_house_nl"
    item_attributes = {
        "brand": "Phone House",
        "brand_wikidata": "Q325113",
        "extras": Categories.SHOP_MOBILE_PHONE.value,
    }
    start_urls = ["https://www.phonehouse.nl/winkels"]
    allowed_domains = ["www.phonehouse.nl"]
    rules = [Rule(LinkExtractor(r"^https:\/\/www\.phonehouse\.nl\/winkels\/phone-house-[\w\-]+$"), "parse")]

    def parse(self, response):
        properties = {
            "ref": response.url,
            "name": response.xpath("//h1/text()").get("").replace("Onze winkel in ", ""),
            "addr_full": clean_address(
                " ".join(response.xpath('//ul[@class="contact-block__list"]//address/text()').getall())
            ),
            "phone": response.xpath('//ul[@class="contact-block__list"]//a[contains(@href, "tel:")]/@href')
            .get("")
            .replace("tel:", ""),
            "email": response.xpath('//ul[@class="contact-block__list"]//a[contains(@href, "mailto:")]/@href')
            .get("")
            .replace("mailto:", ""),
            "website": response.url,
            "opening_hours": OpeningHours(),
        }
        extract_google_position(properties, response)
        hours_text = " ".join(response.xpath('//ul[@class="timing__list"]//text()').getall())
        properties["opening_hours"].add_ranges_from_string(hours_text, days=DAYS_NL)
        yield Feature(**properties)
