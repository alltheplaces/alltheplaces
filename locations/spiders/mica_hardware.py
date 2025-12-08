import re

from scrapy import Spider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class MicaHardwareSpider(Spider):
    name = "mica_hardware"
    start_urls = ["https://www.mica.co.za/store-locator/"]
    item_attributes = {
        "brand": "Mica Hardware",
        "brand_wikidata": "Q116771560",
    }
    skip_auto_cc_domain = True

    def parse(self, response):
        for location in response.xpath('.//ul[@id="js-map-elements"]/li'):
            item = Feature()
            item["ref"] = location.xpath("@data-marker-id").get()

            if lat := location.xpath("@data-marker-lat").get():
                item["lat"] = lat
            else:
                item["lat"] = response.xpath(f'//div[@data-marker="{item["ref"]}"]/@data-markerlat').get()
            if lon := location.xpath("@data-marker-lon").get():
                item["lon"] = lon
            else:
                item["lon"] = response.xpath(f'//div[@data-marker="{item["ref"]}"]/@data-markerlon').get()

            item["name"] = location.xpath("@data-marker-title").get()  # This is used as fascia, not just branch
            item["website"] = location.xpath(".//h2/a/@href").get()
            item["phone"] = "; ".join(location.xpath('.//a[contains(@href, "tel:")]/@href').getall())
            item["addr_full"] = clean_address(
                location.xpath('.//span[@class="store-item store-address"]/text()').getall()
            )

            item["opening_hours"] = OpeningHours()
            for day in location.xpath('.//span[@class="store-item store-hours"]/p/text()').getall():
                day = re.sub(r"(\d)H(\d)", r"\1:\2", day)
                item["opening_hours"].add_ranges_from_string(day)

            yield item
