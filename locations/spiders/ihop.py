import scrapy
from locations.items import GeojsonPointItem
import json
import re


class IHOPSpider(scrapy.Spider):
    name = "ihop"
    allowed_domains = ["restaurants.ihop.com"]
    start_urls = (
        'https://restaurants.ihop.com/',
    )
    location_selector = ".location-careers a::attr('href')"

    def parse(self, response):
        state_urls = response.css(self.location_selector).extract()
        for state_url in state_urls:
            yield scrapy.Request(url=state_url, callback=self.parse_state)

    def parse_state(self, response):
        city_urls = response.css(self.location_selector).extract()
        for city_url in city_urls:
            yield scrapy.Request(url=city_url, callback=self.parse_city)

    def parse_city(self, response):
        location_urls = response.css(self.location_selector).extract()
        for location_url in location_urls:
            yield scrapy.Request(url=location_url, callback=self.parse_location)

    def parse_location(self, response):
        info_jsons = response.css("script[type='application/ld+json']::text").extract()
        info = [x for x in info_jsons if "geo" in x]
        basic_info = json.loads(info[-1])
        if len(response.css(".icon-24")):
            opening_hours = "24/7"
        else:
            hour_nodes = response.css(".hours.openLogo").extract_first()
            days = response.css(".hours.openLogo div::text").extract()
            times = [x[7:-5].replace("\xa0", "") for x in re.findall(r"</div.*<br>", hour_nodes)]
            formatted_times = []
            for day, time in zip(days, times):
                prefix, start_time, end_time = day[:2], *time.split(" - ")
                start_hour, start_minutes = int(start_time[:2]), int(start_time[3:5])
                end_hour, end_minutes = int(end_time[:2]), int(end_time[3:5])
                hours_str = "%s %02d:%02d-%02d:%02d" % (prefix, start_hour, start_minutes, end_hour + 12, end_minutes)
                formatted_times.append(hours_str)
            opening_hours = "; ".join(formatted_times)

        point = {
            "lat": basic_info["geo"]["latitude"],
            "lon": basic_info["geo"]["longitude"],
            "name": basic_info["name"],
            "addr_full": basic_info["address"]["streetAddress"],
            "city": basic_info["address"]["addressLocality"],
            "state": basic_info["address"]["addressRegion"],
            "postcode": basic_info["address"]["postalCode"],
            "country": basic_info["address"]["addressCountry"],
            "phone": basic_info["telephone"],
            "website": basic_info["url"],
            "opening_hours": opening_hours,
            "ref": basic_info["@id"],
        }
        return GeojsonPointItem(**point)
