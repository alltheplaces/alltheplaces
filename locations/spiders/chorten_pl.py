from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature


class ChortenPLSpider(CrawlSpider):
    name = "chorten_pl"
    item_attributes = {}
    start_urls = ["https://chorten.com.pl/sklepy/lista/"]
    rules = [
        Rule(LinkExtractor(allow=[r"/sklepy/lista/p\d+?$"])),
        Rule(LinkExtractor(allow=[r"/sklepy/[\w%_-]+_\d+$"]), callback="parse_store"),
    ]

    def parse_store(self, response: Response, **kwargs):
        address_lines = list(map(str.strip, response.xpath("//address/text()").getall()))
        opening_hours = OpeningHours()
        days_and_hours = list(
            filter(
                lambda h: len(h) > 0,
                map(str.strip, response.xpath("//dl[contains(@class, 'godziny')]/*/text()").getall()),
            )
        )
        for day, hours in zip(days_and_hours[0::2], days_and_hours[1::2]):
            opening_hours.add_ranges_from_string(f"{day} {hours}", days=DAYS_PL)
        properties = {
            "lat": response.xpath("//div[@id='sklep-mapa']/@data-lat").get(),
            "lon": response.xpath("//div[@id='sklep-mapa']/@data-lng").get(),
            "street_address": address_lines[0],
            "postcode": address_lines[1].split(" ")[0],
            "city": " ".join(address_lines[1].split(" ")[1:]),
            "opening_hours": opening_hours,
            "website": response.url,
            "ref": response.url.split("_")[-1],
        }
        returned = Feature(**properties)
        returned["extras"]["shop"] = "yes"
        return returned
