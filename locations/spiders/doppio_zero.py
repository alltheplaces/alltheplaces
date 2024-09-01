from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature, SocialMedia, set_social_media


class DoppioZeroSpider(CrawlSpider):
    name = "doppio_zero"
    item_attributes = {"brand": "Doppio Zero", "brand_wikidata": "Q130214537"}
    allowed_domains = ["doppio.co.za"]
    start_urls = ["https://doppio.co.za/"]
    rules = [Rule(LinkExtractor(allow=r"^https:\/\/doppio.co.za\/restaurant\/.+\/$"), callback="parse")]
    skip_auto_cc_domain = True

    def parse(self, response):
        properties = {
            "ref": response.url,
            "branch": response.xpath('.//div[@class="post-title"]/h1/text()').get(),
            "addr_full": response.xpath('.//div[contains(@class, "restaurant_address")]/text()').get(),
            "phone": "; ".join(response.xpath('.//li[@class="restaurant_telephone"]/a/@href').getall()),
            "email": "; ".join(response.xpath('.//li[@class="restaurant_email"]/a/@href').getall()),
            "website": response.url,
            "opening_hours": OpeningHours(),
        }
        extract_google_position(properties, response)
        properties["opening_hours"].add_ranges_from_string(
            response.xpath('.//div[contains(@class, "restaurant_trading_hours")]/text()').get()
        )
        item = Feature(**properties)
        if (whatsapp := response.xpath('.//li[@class="restaurant_whatsapp"]/a/@href').get()) is not None:
            set_social_media(item, SocialMedia.WHATSAPP, "+" + whatsapp.removeprefix("https://wa.me/"))
        yield item
