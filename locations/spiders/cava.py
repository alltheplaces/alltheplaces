import scrapy

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class CavaSpider(scrapy.Spider):
    name = "cava"
    allowed_domains = ["www.cava.com"]
    item_attributes = {"brand": "Cava", "brand_wikidata": "Q85751038"}
    start_urls = ("https://cava.com/locations/",)

    def parse(self, response):
        state_selectors = response.xpath('.//div[@class="menu-panel-wrapper"]/div[@class="menu-content"]')
        for state_selector in state_selectors:
            yield from self.parse_state(state_selector)

    def parse_state(self, state):
        location_selectors = state.xpath('.//div[@class="vcard"]')
        for location_selector in location_selectors:
            yield from self.parse_location(location_selector)

    def parse_location(self, location):
        non_breaking_space = "\xa0"
        city = location.xpath(".//h3/text()").extract_first()
        street_address = (
            location.xpath('.//div[@class="street-address"]/text()').extract_first().replace(non_breaking_space, " ")
            + ", "
            + location.xpath('.//span[@class="locality"]/text()').extract_first().replace(non_breaking_space, " ")
        )
        state = location.xpath('.//span[@class="region"]/text()').extract_first()
        postcode = location.xpath('.//span[@class="postal-code"]/text()').extract_first()
        phone = location.xpath('.//a[contains(@href, "tel")]/@href').extract_first()
        phone = phone.replace("tel:", "") if phone else ""
        opening_hours = location.xpath('.//p[@class="copy"]/text()').extract_first()
        if opening_hours:
            if "day" not in opening_hours and "Daily" not in opening_hours:
                opening_hours = opening_hours.replace("Hours:", "Hours: Daily, ")
            opening_hours = opening_hours.replace("Hours: ", "").replace("Daily", "Monday - Sunday")
            if "||" in opening_hours:
                opening_hours = opening_hours.split("||")
            else:
                opening_hours = opening_hours.split("//")
            opening_hours = self.parse_opening_hours(opening_hours)

        properties = {
            "ref": street_address,
            "street_address": street_address,
            "city": city,
            "postcode": postcode,
            "state": state,
            "phone": phone,
            "opening_hours": opening_hours,
        }
        yield Feature(**properties)

    def parse_opening_hours(self, timings):
        oh = OpeningHours()

        for timing in timings:
            timing = timing.strip()
            days, times = timing.split(",")

            start_day, end_day = days.split("-") if len(days.split("-")) == 2 else [days, days]
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
        if timing[-2:] == "am":
            timing = timing[:-2]
            if ":" not in timing:
                timing = str(timing) + ":00"
        elif timing[-2:] == "pm":
            timing = timing[:-2]
            if ":" in timing:
                hours, mins = timing.split(":")
                hours = int(hours) + 12
                timing = str(hours) + ":" + str(mins)
            else:
                hours = int(timing) + 12
                timing = str(hours) + ":00"
        return timing
