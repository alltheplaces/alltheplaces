import phonenumbers
from phonenumbers import NumberParseException
from scrapy import Spider

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.hamleys import HAMLEYS_SHARED_ATTRIBUTES
from locations.structured_data_spider import extract_email, extract_phone


class HamleysZASpider(Spider):
    name = "hamleys_za"
    start_urls = ["https://hamleys.co.za/stores/"]
    item_attributes = HAMLEYS_SHARED_ATTRIBUTES

    def parse(self, response):
        for location in response.xpath('.//div[@data-widget_type="image-box.default"]'):
            if "hidden" in location.xpath("ancestor::section[@class][position()=1]/@class").get():
                continue
            item = Feature()
            item["ref"] = location.xpath("@data-id").get()
            item["branch"] = location.xpath(".//h3/a/text()").get()

            address_lines = location.xpath('.//p[@class="elementor-image-box-description"]/text()').getall()
            for line in address_lines:
                if "@" in line:
                    address_lines.remove(line)
                try:
                    ph = phonenumbers.parse(line, "ZA")
                    if phonenumbers.is_valid_number(ph):
                        address_lines.remove(line)
                except NumberParseException:
                    pass
            item["addr_full"] = clean_address(address_lines)

            extract_google_position(item, response)
            extract_email(item, location)
            extract_phone(item, location)
            yield item
