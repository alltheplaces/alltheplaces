from scrapy import Request, Spider

from locations.hours import DAYS_PT, DELIMITERS_PT, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class BoloDaMadreBRSpider(Spider):
    name = "bolo_da_madre_br"
    item_attributes = {"brand": "Bolo da Madre", "brand_wikidata": "Q121322483"}
    # allowed_domains = ["www.a1.net"]
    start_urls = ["https://bolodamadre.com.br/onde-encontrar/"]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse_store_list)

    def parse_store_list(self, response):
        locations = response.xpath("//div[contains(@class, 'list-places')]/div[contains(@class, 'place')]")
        for location in locations:
            name = location.xpath("h3/strong/text()").get()

            address_hours = location.xpath("div[@class='address-hours']/p/text()").getall()

            oh = OpeningHours()
            oh.add_ranges_from_string(address_hours[3], days=DAYS_PT, delimiters=DELIMITERS_PT)
            if 4 in address_hours:
                oh.add_ranges_from_string(address_hours[4], days=DAYS_PT, delimiters=DELIMITERS_PT)
            if 5 in address_hours:
                oh.add_ranges_from_string(address_hours[5], days=DAYS_PT, delimiters=DELIMITERS_PT)

            yield Feature(
                {
                    "ref": name,
                    "name": name,
                    "addr_full": clean_address([address_hours[0], address_hours[1]]),
                    "phone": location.xpath("p/span[@class='whats-phone']/a/text()").get(),
                    "opening_hours": oh,
                }
            )
