import re

import scrapy

from locations.linked_data_parser import LinkedDataParser


class UhaulSpider(scrapy.Spider):
    name = "uhaul"
    item_attributes = {"brand": "U-Haul", "brand_wikidata": "Q7862902"}
    allowed_domains = ["www.uhaul.com"]

    start_urls = ("https://www.uhaul.com/Locations/US_and_Canada/",)
    wanted_types = ["SelfStorage", "LocalBusiness"]

    def parse(self, response):
        for cell in response.xpath('//ul/li[@class="cell"]/a/@href'):
            yield scrapy.Request(url=response.urljoin(cell.extract()))

        for store_nav in response.xpath('//ul/li/ul[@class="sub-nav"]'):
            # Each store nav can have multiple services, each with a link under the sub-nav ul.
            # We want to pick the first one to get to a store details page.
            store_url = store_nav.xpath(".//a/@href").extract_first()

            yield scrapy.Request(url=response.urljoin(store_url), callback=self.parse_store)

    def parse_store(self, response):
        item = LinkedDataParser.parse(response, "SelfStorage")
        if item is None:
            item = LinkedDataParser.parse(response, "LocalBusiness")
            if item is None:
                return

        item["ref"] = response.url.split("/")[-2]

        hour_elements = response.xpath(
            '//div[@class="callout flat radius hide-for-native"]/ul/li[@itemprop="openinghours"]/@datetime'
        )
        item["opening_hours"] = self.hours(hour_elements)
        if "lat" in item and "lon" in item:
            # Can skip the call to the next one if this page happened to have lat/lon
            yield item

        yield scrapy.Request(
            url="https://www.uhaul.com/Locations/Directions-to-%s/" % item["ref"],
            callback=self.parse_directions,
            meta={"item": item},
        )

    def hours(self, store_hours):
        opening_hours = []

        for data in store_hours.extract():
            day_text = data.split(":")[0]
            hours_text = data.split(":")[1]

            if "-" in day_text:
                f_day = day_text.split("-")[0][:2]
                t_day = day_text.split("-")[1][:2]
                day = "{}-{}".format(f_day, t_day)
            else:
                day = day_text[:2]

            if "-" in hours_text:
                f_hour = self.normalize_time(hours_text.split("-")[0].strip(), True)
                t_hour = self.normalize_time(hours_text.split("-")[1].strip(), False)
                hours = "{}-{}".format(f_hour, t_hour)
            else:
                hours = "Closed"

            opening_hours.append("{} {}".format(day, hours))

        return "; ".join(opening_hours)

    def normalize_time(self, time_str, open):
        match = re.search(r"([0-9]{1,2}):([0-9]{1,2})", time_str)
        if not match:
            match = re.search(r"([0-9]{1,2})", time_str)
            h = match.group()
            m = "0"
        else:
            h, m = match.groups()

        return "%02d:%02d" % (int(h) + 12 if not open else int(h), int(m))

    def parse_directions(self, response):
        script_str = response.xpath('//script/text()[contains(.,"mapPins")]').get()
        matches = re.search(r'"lat":([\-\d\.]*),"long":([\-\d\.]*),', script_str)
        lat, lon = matches.groups() if matches else (None, None)

        item = response.meta["item"]
        item["lat"] = lat
        item["lon"] = lon

        yield item
