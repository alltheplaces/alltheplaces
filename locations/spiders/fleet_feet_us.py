import re

from scrapy import Spider

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class FleetFeetUSSpider(Spider):
    name = "fleet_feet_us"
    item_attributes = {"brand": "Fleet Feet", "brand_wikidata": "Q117062761"}
    start_urls = ["https://www.fleetfeet.com/locations"]

    def parse(self, response, **kwargs):
        for location in response.xpath('//div[@class="location"]'):
            item = Feature()
            item["lat"] = location.xpath("./@data-lat").get()
            item["lon"] = location.xpath("./@data-lng").get()
            item["branch"] = location.xpath("./h3/text()").get()
            item["ref"] = item["website"] = response.urljoin(location.xpath(".//*[@href][last()]/@href").get())

            if addr := location.xpath('./p[@class="address"]/text()').getall():
                if m := re.search(r"([. \w]+), (\w\w) (\d+)", addr[1].strip()):
                    item["street_address"] = addr[0]
                    item["city"] = m.group(1)
                    item["state"] = m.group(2)
                    item["postcode"] = m.group(3)
                else:
                    item["street_address"] = merge_address_lines([addr[0], addr[1]])

            yield item
