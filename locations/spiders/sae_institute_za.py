from scrapy import Spider

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.sae_institute_au import SAE_INSTITUTE_SHARED_ATTRIBUTES


# Also used by UK, US
class SaeInstitueZASpider(Spider):
    name = "sae_institute_za"
    start_urls = ["https://www.sae.edu.za/contact-us/"]
    item_attributes = SAE_INSTITUTE_SHARED_ATTRIBUTES
    no_refs = True

    def parse(self, response):
        for location in response.xpath('.//div[@class="col"]'):
            item = Feature()
            extract_google_position(item, location)
            item["branch"] = location.xpath(".//h3/text()").get()
            item["addr_full"] = clean_address(location.xpath('string(.//i[contains(@class,"bi-geo-alt")]/..)').get())
            item["phone"] = location.xpath('.//a[contains(@href, "tel")]/@href').get()
            item["email"] = location.xpath('.//a[contains(@href, "mailto")]/@href').get()
            yield item
