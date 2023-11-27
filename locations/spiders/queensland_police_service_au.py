from scrapy import Spider

from locations.hours import OpeningHours
from locations.items import Feature


class QueenslandPoliceServiceAUSpider(Spider):
    name = "queensland_police_service_au"
    allowed_domains = ["www.police.qld.gov.au"]
    start_urls = ["https://www.police.qld.gov.au/stations"]

    def parse(self, response):
        stations = {}
        locations = response.xpath('//div[@id="stations-location"]')
        for location in locations:
            properties = {
                "ref": location.xpath('.//@data-link').get().strip(),
                "name": location.xpath('.//@data-name').get().strip(),
                "lat": location.xpath('.//@data-lat').get().strip(),
                "lon": location.xpath('.//@data-lon').get().strip(),
                "addr_full": location.xpath('.//@data-address').get().strip(),
                "website": location.xpath('.//@data-link').get().strip(),
            }
            stations[properties["ref"]] = properties
        locations2 = response.xpath('//div[@class="one-location-card"]')
        for location2 in locations2:
            properties2 = {
                "ref": location2.xpath('.//h5/a/@href').get().strip(),
                "name": location2.xpath('.//h5/a/text()').get().strip(),
                "addr_full": " ".join(filter(None, location2.xpath('.//div[@class="row"]/div[@class="cols big"]//text()').getall())).strip(),
                "phone": location2.xpath('.//a[contains(@href, "tel:")]/@href').get().replace("tel:", "").strip(),
            }
            hours_string = " ".join(filter(None, location2.xpath('.//div[@class="row"]/div[@class="cols smaller"][1]//text()').getall())).strip()
            properties["opening_hours"] = OpeningHours()
            properties["opening_hours"].add_ranges_from_string(hours_string)
            stations[properties["ref"]].update(properties2)
        for station in stations:
            yield Feature(**station)
