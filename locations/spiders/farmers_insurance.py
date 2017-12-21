import scrapy
from locations.items import GeojsonPointItem
import json


class FarmersInsuranceSpider(scrapy.Spider):
    name = "farmers-insurance"

    start_urls = ["https://agents.farmers.com/"]

    def get_hours(self, hours_json):
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

            point = {
                "lat": lat.strip(),
                "lon": lon.strip(),
                "city": agent.css(".c-address-city::text").extract_first(),
                "state": agent.css(".c-address-state::text").extract_first(),
                "postcode": agent.css(".c-address-postal-code::text").extract_first(),
                "country": agent.css(".c-address-country-name::text").extract_first(),
                "phone": agent.css(".location-phone a::text").extract_first(),
                "website": response.urljoin(agent.css(".location-title-link").xpath("@href").extract_first()),
                "ref": agent_number,
                "name": "Farmers Insurance Agent - {}, Agent #{}".format(agent_name, agent_number),
                "addr_full": " ".join([row.css("::text").extract_first() for row in agent.css(".c-AddressRow")][:2]),
                "opening_hours": self.get_hours(hours_json),
            }

            yield GeojsonPointItem(**point)
