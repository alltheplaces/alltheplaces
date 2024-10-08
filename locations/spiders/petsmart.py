import re
import urllib.parse

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature

day_mapping = {
    "MON": "Mo",
    "TUE": "Tu",
    "WED": "We",
    "THU": "Th",
    "FRI": "Fr",
    "SAT": "Sa",
    "SUN": "Su",
}


def convert_24hour(time):
    """
    Takes 12 hour time as a string and converts it to 24 hour time.
    """

    time = time.replace(".", ":")

    if len(time[:-2].split(":")) < 2:
        hour = time[:-2]
        minute = "00"
    else:
        hour, minute = time[:-2].split(":")

    if time[-2:] == "AM":
        time_formatted = hour + ":" + minute
    elif time[-2:] == "PM":
        time_formatted = str(int(hour) + 12) + ":" + minute

    if time_formatted in ["24:00", "0:00", "00:00"]:
        time_formatted = "23:59"

    return time_formatted


class PetsmartSpider(scrapy.Spider):
    name = "petsmart"
    item_attributes = {"brand": "PetSmart", "brand_wikidata": "Q3307147"}
    allowed_domains = ["petsmart.com", "petsmart.ca"]
    start_urls = (
        "https://www.petsmart.com/store-locator/all/",
        "https://www.petsmart.ca/store-locator/all/",
    )

    def parse(self, response):
        for state_url in response.xpath('//*[@class="all-states-list container"]//@href').extract():
            yield scrapy.Request(response.urljoin(state_url), callback=self.parse_state)

    def parse_state(self, response):
        for href in response.xpath('//a[@class="store-details-link"]/@href').extract():
            yield scrapy.Request(response.urljoin(href), callback=self.parse_store)

    def parse_store(self, response):
        country = None
        if "petsmart.ca" in response.url:
            country = "CA"
        elif "petsmart.com" in response.url:
            country = "US"

        ref = re.search(r"-store(\d+)", response.url).group(1)

        map_url = response.xpath('//img/@src[contains(.,"staticmap")]').extract_first()
        [lat_lon] = urllib.parse.parse_qs(urllib.parse.urlparse(map_url).query)["center"]
        lat, lon = lat_lon.split(",")

        properties = {
            "name": response.xpath("//h1/text()").extract_first(),
            "addr_full": response.xpath('normalize-space(//p[@class="store-page-details-address"])').extract_first(),
            "lat": lat,
            "lon": lon,
            "phone": response.xpath('normalize-space(//p[@class="store-page-details-phone"])').extract_first(),
            "country": country,
            "ref": ref,
            "website": response.url,
        }

        hours_elements = response.xpath('//*[@itemprop="OpeningHoursSpecification"]')
        if hours_elements:
            properties["opening_hours"] = self.parse_hours(hours_elements)

        yield Feature(**properties)

    def parse_hours(self, elements):
        opening_hours = OpeningHours()

        days = elements.xpath('.//span[@itemprop="dayOfWeek"]/text()').extract()

        today = (set(day_mapping) - set(days)).pop()
        days.remove("TODAY")
        days.insert(0, today)
        open_hours = elements.xpath('.//time[@itemprop="opens"]/@content').extract()
        close_hours = elements.xpath('.//time[@itemprop="closes"]/@content').extract()

        store_hours = {z[0]: list(z[1:]) for z in zip(days, open_hours, close_hours)}

        for day, hours in store_hours.items():
            if "CLOSED" in hours:
                continue
            opening_hours.add_range(
                day=day_mapping[day],
                open_time=convert_24hour(hours[0]),
                close_time=convert_24hour(hours[1]),
            )
        return opening_hours.as_opening_hours()
