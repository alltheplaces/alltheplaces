from scrapy import Spider

from locations.items import Feature
from locations.spiders.mcdonalds import McDonaldsSpider


class McDonaldsZASpider(Spider):
    name = "mcdonalds_za"
    item_attributes = McDonaldsSpider.item_attributes
    start_urls = ["https://www.mcdonalds.co.za/templates/_layout/ajax_calls/get_all_locations.php?lat=0&long=0"]

    def parse(self, response, **kwargs):
        for location in response.xpath('//div[@class="store_listing_con"]'):
            item = Feature()
            item["website"] = item["ref"] = location.xpath(".//a/@href").get()

            if item["website"] == "https://www.mcdonalds.co.za/location/mcdonalds-head-office":
                continue

            item["name"] = location.xpath(".//h5/text()").get()
            item["addr_full"] = location.xpath(".//p/text()").get()
            item["phone"] = (
                location.xpath('.//span[contains(., "Contact Number:")]/text()')
                .get()
                .replace("Contact Number:", "")
                .strip()
            )
            item["email"] = location.xpath('.//span[contains(., "Email:")]/text()').get().replace("Email:", "").strip()

            yield item
