import scrapy
import json
import re
from locations.hours import OpeningHours
from locations.items import GeojsonPointItem

DAY_MAPPING = {
    "Sunday": "Su",
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
}


class CandaPostSpider(scrapy.Spider):
    name = "canadapost"
    item_attributes = {"brand": "Canada Post"}
    allowed_domains = ["canadapost.ca"]
    start_urls = (
        "https://maps.googleapis.com/maps/api/js/KmlOverlayService.GetOverlays?1shttp%3A%2F%2Fwww.canadapost.ca%2Fcpo%2Fmc%2Fapp%2Fpersonal%2Ffpo%2Fgeodata%2Fcpc-outlets-en.kmz%3F14&callback=_xdc_._vjm4rb&client=gme-innovapost1&token=61596",
    )

    def parse(self, response):
        pdata = json.dumps(response.text)
        postids = re.findall('(00.+?)\\\\"]', pdata)

        url = "https://www.canadapost.ca/cpotools/apps/fpo/personal/findPostOfficeDetail?outletId={}"

        for postid in postids:
            try:
                yield scrapy.Request(url.format(postid), callback=self.parse_office)
            except ValueError:
                continue

    def parse_hours(self, days, hours):
        opening_hours = OpeningHours()

        # Some listed hours do not follow a consistent scrape-able pattern, so they've been excluded.
        for d, h in zip(days, hours):
            d = DAY_MAPPING[d]
            h = "".join(h).replace(" ", "")
            if h == "-":
                continue
            try:
                open_time, close_time = h.split("-")
            except ValueError:
                continue
            try:
                opening_hours.add_range(
                    day=d,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H:%M",
                )
            except ValueError:
                continue

        return opening_hours.as_opening_hours()

    def parse_office(self, response):
        try:
            addr_parts = response.xpath(
                '//*[@id="results"]/div/div[1]/address/p[1]/text()'
            ).extract()
            addr_parts = list(
                filter(None, [l.strip().replace("\xa0", " ") for l in addr_parts])
            )
            city_state = addr_parts.pop()
            name = addr_parts.pop(0)
            addr = " ".join(addr_parts)
            match = re.search(r"([\w\s]+)\s([A-Z]{2})\s+(\w{3}\s\w{3})", city_state)
            try:
                city, state, postcode = match.groups()
            except AttributeError:
                return
        except IndexError:
            return

        properties = {
            "ref": response.xpath(
                '//*[@id="results"]/div/div[1]/address/p[1]/text()[1]'
            ).extract_first(),
            "name": name,
            "addr_full": addr,
            "city": city,
            "state": state,
            "postcode": postcode,
            "lat": response.xpath(
                '//*[@id="fpoDetailForm:latitude"]/@value'
            ).extract_first(),
            "lon": response.xpath(
                '//*[@id="fpoDetailForm:longitude"]/@value'
            ).extract_first(),
            "website": response.xpath('//*[@id="selectme"]/text()').extract_first(),
        }
        hours = self.parse_hours(
            days=response.xpath("//table//tbody//tr//td[1]/text()").extract(),
            hours=response.xpath("//table//tbody//tr//td[2]/text()").extract(),
        )

        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)
