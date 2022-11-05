import scrapy

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import GeojsonPointItem


class SafeliteSpider(scrapy.Spider):
    name = "safelite"
    allowed_domains = ["www.safelite.com"]
    item_attributes = {"brand": "Safelite", "brand_wikidata": "Q28797369"}
    start_urls = ("https://www.safelite.com/store-locator/store-locations-by-state",)

    def parse(self, response):
        state_urls = response.xpath(
            './/div[@class="state-store-list"]/a/@href'
        ).extract()
        for state_url in state_urls:
            yield scrapy.Request(
                f"https://www.safelite.com{state_url}", callback=self.parse_location
            )

    def parse_location(self, response):
        try:
            addr_full = (
                response.xpath('.//div[@class="content-block"]')[1]
                .xpath(".//p/text()")
                .extract_first()
            )
            addr_full = addr_full.split(",")
            street_address = ", ".join(addr_full[:-2])
            city = addr_full[-2].strip()
            state_postcode = addr_full[-1].strip()
            state, postcode = state_postcode.strip().split(" ")
            state = state.strip()
            addr_full = ", ".join(addr_full)
            lat = response.xpath(
                './/div[@class="store-map"]/@data-start-lat'
            ).extract_first()
            lon = response.xpath(
                './/div[@class="store-map"]/@data-start-lon'
            ).extract_first()
        except:
            addr_full = response.xpath(".//h1/text()").extract_first()
            street_address = None
            city, state = addr_full.split(",")
            city = city.strip()
            state = state.strip()
            postcode = None
            lat = None
            lon = None
        opening_hours = response.xpath(
            './/div[@class="shop-container "]/p/text()'
        ).extract()
        opening_hours = [timing.strip() for timing in opening_hours]
        properties = {
            "ref": response.url,
            "street_address": street_address,
            "city": city,
            "state": state,
            "postcode": postcode,
            "opening_hours": self.parse_opening_hours(opening_hours),
            "website": response.url,
            "lat": lat,
            "lon": lon,
        }
        yield GeojsonPointItem(**properties)

    def parse_opening_hours(self, timings):
        timings = [timing for timing in timings if "closed" not in timing.lower()]
        oh = OpeningHours()
        for timing in timings:
            timing = timing.strip()
            timing = timing.replace(":", ",", 1)
            days, times = timing.split(",")
            start_day, end_day = (
                days.split("-") if len(days.split("-")) == 2 else [days, days]
            )
            start_day, end_day = start_day.strip(), end_day.strip()
            start_time, end_time = times.split("-")
            start_time = self.parse_timings(start_time.strip())
            end_time = self.parse_timings(end_time.strip())
            curr_day_index = DAYS_FULL.index(start_day)
            while curr_day_index <= DAYS_FULL.index(end_day):
                curr_day_index += 1
                oh.add_range(DAYS_FULL[curr_day_index - 1], start_time, end_time)

        return oh.as_opening_hours()

    def parse_timings(self, timing):
        if timing[-3:] == " AM":
            timing = timing[:-3]
            if ":" not in timing:
                timing = str(timing) + ":00"
        elif timing[-3:] == " PM":
            timing = timing[:-3]
            if ":" in timing:
                hours, mins = timing.split(":")
                hours = int(hours) + 12
                timing = str(hours) + ":" + str(mins)
            else:
                hours = int(timing) + 12
                timing = str(hours) + ":00"
        return timing
