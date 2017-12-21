import scrapy
from scrapy.spiders import BaseSpider
from locations.items import GeojsonPointItem
import json
import re
from io import StringIO
from scrapy.http import HtmlResponse

def get_hours(hours_json):
    days = json.loads(hours_json)
    out_hours = []

    for day in days:
        start_day = day["day"][:2].title()
        intervals = day["intervals"]
        hours = ["%04d-%04d" % (interval["start"], interval["end"]) for interval in intervals]
        if len(intervals):
            out_hours.append("{} {}".format(start_day, ",".join(hours)))
    if len(out_hours):
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
            agent_number = agent.xpath("@data-agent-number").extract_first()
            agent_name = agent.css(".location-title-link::text").extract_first()
            hours_json = agent.css(".c-location-hours-details-wrapper").xpath("@data-days").extract_first()

            point = {}
            point["lat"] = lat.strip()
            point["lon"] = lon.strip()
            point["city"] = agent.css(".c-address-city::text").extract_first()
            point["state"] = agent.css(".c-address-state::text").extract_first()
            point["postcode"] = agent.css(".c-address-postal-code::text").extract_first()
            point["country"] = agent.css(".c-address-country-name::text").extract_first()
            point["phone"] = agent.css(".location-phone a::text").extract_first()
            point["website"] = response.urljoin(agent.css(".location-title-link").xpath("@href").extract_first())
            point["ref"] = agent_number
            point["name"] = "Farmers Insurance Agent - {}, Agent #{}".format(agent_name, agent_number)
            point["addr_full"] = " ".join([row.css("::text").extract_first() for row in agent.css(".c-AddressRow")][:2])
            point["opening_hours"] = get_hours(hours_json)
            yield GeojsonPointItem(
                **point
            )
