import scrapy
import re
from urllib.parse import urlparse

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem

ALL_DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class DickeysBarbecuePitSpider(scrapy.Spider):
    name = "dickeys_barbecue_pit"
    item_attributes = {"brand": "Dickey's Barbecue Pit", "brand_wikidata": "Q19880747"}
    allowed_domains = ["dickeys.com"]
    download_delay = 0.5
    start_urls = ("https://www.dickeys.com/location/search-by-state",)

    def parse(self, response):
        directory_links = response.xpath('//a[@class="state-links"]/@href').extract()
        for link in directory_links:
            yield scrapy.Request(response.urljoin(link), callback=self.parse)

        regex_phone_prefix = re.compile(r"^\s*Telephone\:\s*(.+)$")

        all_restaurants = response.xpath(
            '//*[@itemtype="http://schema.org/Restaurant"]'
        )
        for restaurant in all_restaurants:

            properties = {
                "name": restaurant.xpath('.//*[@itemprop="name"]/text()').get(),
                "addr_full": restaurant.xpath(
                    './/*[@itemprop="streetAddress"]/text()'
                ).get(),
                "city": restaurant.xpath(
                    './/*[@itemprop="addressLocality"]/text()'
                ).get(),
                "state": restaurant.xpath(
                    './/*[@itemprop="addressRegion"]/text()'
                ).get(),
                "postcode": restaurant.xpath(
                    './/*[@itemprop="postalCode"]/text()'
                ).get(),
                "phone": restaurant.xpath(
                    './/a[starts-with(text(), "Telephone:")]/text()'
                ).get(),
                "website": response.url,
            }

            # URLs with details of all restaurants in a given city look like:
            # '/location/search-by-city/<num>/<city-name>', where:
            #
            # <num> appears to be a number associated with the state containing the city
            # <city-name> is the name of the city.
            #
            # Strip off the '/location/search-by-city' prefix, then append the street address we found for each
            # restaurant.  Use this as the unique ID of the restaurant in the crawl, as no other
            # reliable ID seems to appear in the data.
            ref = urlparse(response.url).path.split("/", maxsplit=3)[3]
            properties["ref"] = "_".join([ref, properties["addr_full"]])

            # If phone has a 'Telephone: ' prefix, strip it away.
            match_phone = re.search(regex_phone_prefix, properties["phone"])
            if match_phone:
                properties["phone"] = match_phone.groups()[0]

            # Some fields may have leading/trailing space.  We've seen that city often has both
            # trailing comma and space.
            for key in properties:
                properties[key] = properties[key].strip(", ")

            opening_hours = self.parse_hours(restaurant)
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield GeojsonPointItem(**properties)

    def parse_hours(self, restaurant_item):
        opening_hours = OpeningHours()
        opening_hours_str = restaurant_item.xpath(
            './/*[@itemprop="openingHours"]/@content'
        ).get()

        if opening_hours_str:
            regex = re.compile(
                r"(.+)\:\s*(\d{1,2}:\d{2} [A|P][M])\s*-\s*(\d{1,2}:\d{2} [A|P][M])",
                flags=re.IGNORECASE,
            )

            # Opening hours specifications may look like either of the following:
            #
            #   Open Daily: 11:00 AM - 9:00 PM
            #   Mon-Thur: 11:00 AM - 8:00 PM,Fri-Sat: 11:00 AM - 9:00 PM,Sunday: 11:00 AM - 8:00 PM
            #
            for hours in opening_hours_str.split(","):
                hours = hours.strip()

                match = re.search(regex, hours)
                if match:
                    day_range = match.group(1)
                    open_time = match.group(2)
                    close_time = match.group(3)

                    if close_time == "00:00":
                        close_time = "23:59"

                    for day in self.get_days(day_range):
                        opening_hours.add_range(
                            day, open_time, close_time, time_format="%I:%M %p"
                        )

        return opening_hours.as_opening_hours()

    def get_days(self, day_range_str):
        day_range_str = day_range_str.casefold()

        # Most stores list same opening hours for every day of the week: "Open Daily: ..."
        if day_range_str == "open daily":
            return ALL_DAYS
        # A few store list different hours for different days:
        else:
            start_and_end = day_range_str.split("-")

            # Handle cases like the "Sunday" in "Sunday: ..."
            if len(start_and_end) == 1:
                return [self.day_mapping(start_and_end[0])]
            # Handle cases like the "Mon-Thur" in "Mon-Thur: ..."
            elif len(start_and_end) == 2:
                try:
                    start_index = ALL_DAYS.index(self.day_mapping(start_and_end[0]))
                    end_index = ALL_DAYS.index(self.day_mapping(start_and_end[1]))

                    if start_index < end_index:
                        return ALL_DAYS[start_index : end_index + 1]
                except ValueError:
                    # In case we extract an unexpected string as a day of the week
                    return None
            # In case the day/day range doesn't look like what we expect
            else:
                return None

    def day_mapping(self, day_str):
        day_str = day_str.casefold()

        if "sunday".startswith(
            day_str,
        ):
            return "Su"
        elif "monday".startswith(day_str):
            return "Mo"
        elif "tuesday".startswith(day_str):
            return "Tu"
        elif "wednesday".startswith(day_str):
            return "We"
        elif "thursday".startswith(day_str):
            return "Th"
        elif "friday".startswith(day_str):
            return "Fr"
        elif "saturday".startswith(day_str):
            return "Sa"

        return None
