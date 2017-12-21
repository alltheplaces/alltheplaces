import scrapy
from scrapy.spiders import BaseSpider
from locations.items import GeojsonPointItem
import json
import re
from io import StringIO
from scrapy.http import HtmlResponse

_ = [{"day": "MONDAY", "intervals": [{"end": 1730, "start": 800}], "through": "FRIDAY"},
 {"day": "TUESDAY", "intervals": [{"end": 1730, "start": 800}]},
 {"day": "WEDNESDAY", "intervals": [{"end": 1730, "start": 800}]},
 {"day": "THURSDAY", "intervals": [{"end": 1730, "start": 800}]},
 {"day": "FRIDAY", "intervals": [{"end": 1730, "start": 800}]},
 {"day": "SATURDAY", "intervals": [], "through": "SUNDAY"}, {"day": "SUNDAY", "intervals": []}]


def get_hours(hours_json):
    days = json.loads(hours_json)

    for day in days:
        if "through" in day.keys():
            range = "{}-{}".format()

    out_hours = []

    return "; ".join(out_hours)


class FarmersInsuranceSpider(scrapy.Spider):
    name = "farmers-insurance"

    start_urls = ["https://agents.farmers.com/"]

    def parse(self, response):
        paths = [response.urljoin(x.xpath("@href").extract_first()) for x in
                 response.css(".c-directory-list-content-item-link")]
        for path in paths:
            yield scrapy.Request(url=path, callback=self.parse_cities)

    def parse_cities(self, response):
        paths = [response.urljoin(x.xpath("@href").extract_first()) for x in
                 response.css(".c-directory-list-content-item-link")]
        for path in paths:
            yield scrapy.Request(url=path, callback=self.parse_agents)

    def parse_agents(self, response):
        for agent in response.css(".location-item"):
            coords = agent.xpath("@data-coordinates").extract_first(default=",")
            lat, lon = coords.split(",")
            agent_number = agent.xpath("data-agent-number").extract_first()
            point = dict(lat=lat,
                         lon=lon,
                         name="Farmers Insurance Agent - {}, Agent #{}".format(
                             agent.css(".location-title-link::text").extract_first(), agent_number),
                         addr_full=" ".join(
                             [row.css("::text").extract_first() for row in agent.css(".c-AddressRow")][:2]),
                         city=agent.css(".c-address-city::text").extract_first(),
                         state=agent.css(".c-address-state::text").extract_first(),
                         postcode=agent.css(".c-address-postal-code::text").extract_first(),
                         country=agent.css(".c-address-country-name::text").extract_first(),
                         phone=agent.css(".location-phone a::text").extract_first(),
                         website=response.urljoin(agent.css(".location-title-link").xpath("@href").extract_first()),
                         opening_hours=get_hours(agent.css(".c-location-hours-details-wrapper")),
                         ref=agent_number,
                         )
            yield GeojsonPointItem(
                **point
            )


# so that I can use pdb
if __name__ == "__main__":
    from scrapy.crawler import CrawlerProcess

    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
    })

    process.crawl(FarmersInsuranceSpider)
    process.start()  # the script will block here until the crawling is finished
