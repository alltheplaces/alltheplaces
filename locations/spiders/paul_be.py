from scrapy import Spider

from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature
from locations.spiders.paul_fr import PAUL_SHARED_ATTRIBUTES


class PaulBESpider(Spider):
    name = "paul_be"
    item_attributes = PAUL_SHARED_ATTRIBUTES
    start_urls = ["https://www.paul-belgium.be/fr/find-a-paul"]

    def parse(self, response):
        for location in response.xpath('.//div[contains(@class,"geolocation-location")]'):
            item = Feature()
            item["ref"] = location.xpath("@id").get()
            item["lat"] = location.xpath("@data-lat").get()
            item["lon"] = location.xpath("@data-lng").get()
            item["branch"] = location.xpath("string(.//h2)").get().strip()

            item["website"] = "https://www.paul-belgium.be" + location.xpath(".//h2/a/@href").get().replace("/fr/", "/")
            item["extras"]["website:fr"] = item["website"].replace(".be/", ".be/fr/")
            item["extras"]["website:nl"] = item["website"].replace(".be/", ".be/nl/")

            item["street_address"] = location.xpath('.//span[@class="address-line1"]/text()').get()
            item["city"] = location.xpath('.//span[@class="locality"]/text()').get()
            item["postcode"] = location.xpath('.//span[@class="postal-code"]/text()').get()
            item["country"] = location.xpath('.//span[@class="country"]/text()').get()

            item["image"] = "https://www.paul-belgium.be/" + response.xpath('.//div[@itemprop="image"]/img/@src').get()
            item["phone"] = location.xpath('.//a[contains(@href, "tel:")]/@href').get()

            item["opening_hours"] = OpeningHours()
            for times in location.xpath('.//meta[@itemprop="openingHours"]/@content').getall():
                item["opening_hours"].add_ranges_from_string(times, days=DAYS_FR)

            yield item
