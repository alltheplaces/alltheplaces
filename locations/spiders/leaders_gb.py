from urllib.parse import urljoin

from scrapy.spiders import Spider

from locations.items import Feature
from locations.structured_data_spider import extract_email, extract_phone


class LeadersGBSpider(Spider):
    name = "leaders_gb"
    item_attributes = {"brand": "Leaders", "brand_wikidata": "Q111522674"}
    start_urls = ["https://www.leaders.co.uk/contact-us"]

    def parse(self, response, **kwargs):
        for location in response.xpath(
            '//div[contains(@class, "branch-dept-Sales") or contains(@class, "branch-dept-Lettings")]'
        ):
            item = Feature()
            item["addr_full"] = location.xpath("./p/text()").get()

            if "Covering" in item["addr_full"]:
                continue

            item["ref"] = location.xpath("./@data-history-node-id").get()
            item["image"] = urljoin(response.url, location.xpath("./img/@src").get())
            item["lat"], item["lon"] = location.xpath(".//@data-location").get().split(",")
            item["name"] = location.xpath("./h5/span/text()").get()
            extract_email(item, location)
            extract_phone(item, location)
            item["website"] = urljoin(response.url, location.xpath('.//p[@class="branch-link"]/a/@href').get())

            yield item
