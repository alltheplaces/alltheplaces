import json
import scrapy
import re
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class CVSSpider(scrapy.Spider):

    name = "cvs"
    item_attributes = {"brand": "CVS", "brand_wikidata": "Q2078880"}
    allowed_domains = ["www.cvs.com"]
    download_delay = 0.5
    start_urls = ("https://www.cvs.com/store-locator/cvs-pharmacy-locations",)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for group in hours:
            if "closed" in group:
                continue
            if "open 24 hours" in group:
                days = re.search(r"([a-zA-Z\-]+)\s+open 24 hours", group).groups()[0]
                open_time, close_time = "00:00:00", "23:59:00"
            else:
                try:
                    days, open_time, close_time = re.search(
                        r"([a-zA-Z\-]+)\s+([\d:\sapm]+)-([\d:\sapm]+)", group
                    ).groups()
                except AttributeError:
                    continue  # no hours listed, just day
            try:
                start_day, end_day = days.split("-")
            except ValueError:
                start_day, end_day = days, days
            for day in DAYS[DAYS.index(start_day) : DAYS.index(end_day) + 1]:
                if "m" in open_time:
                    open_time = open_time.strip(" apm") + ":00"
                if "m" in close_time:
                    close_time = close_time.strip(" apm") + ":00"
                opening_hours.add_range(
                    day=day,
                    open_time=open_time.strip(),
                    close_time=close_time.strip(),
                    time_format="%H:%M:%S",
                )

        return opening_hours.as_opening_hours()

    def parse_stores(self, response):
        try:
            data = json.loads(
                response.xpath(
                    '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
                ).extract_first()
            )[0]
        except json.decoder.JSONDecodeError:
            # one malformed json body on this store:
            # https://www.cvs.com/store-locator/cvs-pharmacy-address/84+South+Avenue+tops+Plaza+-Hilton-NY-14468/storeid=5076
            data = response.xpath(
                '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
            ).extract_first()
            data = re.sub(r'"tops Plaza\s*"', "", data)
            data = json.loads(data)[0]
        except TypeError:
            return  # empty store page

        properties = {
            "name": data["name"],
            "ref": re.search(r".+/?storeid=(.+)", response.url).group(1),
            "addr_full": data["address"]["streetAddress"].strip(", "),
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": data["address"]["addressCountry"],
            "phone": data["address"].get("telephone"),
            "website": data.get("url") or response.url,
            "lat": data["geo"]["latitude"] or None,
            "lon": data["geo"]["longitude"] or None,
        }

        hours = self.parse_hours(data["openingHours"])
        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse_city_stores(self, response):
        stores = response.xpath('//div[@class="each-store"]')

        for store in stores:

            direction = store.xpath(
                'normalize-space(.//span[@class="store-number"]/a/@href)'
            ).extract_first()
            if direction:
                yield scrapy.Request(
                    response.urljoin(direction), callback=self.parse_stores
                )

    def parse_state(self, response):
        city_urls = response.xpath('//div[@class="states"]/ul/li/a/@href').extract()
        for path in city_urls:
            yield scrapy.Request(
                response.urljoin(path), callback=self.parse_city_stores
            )

    def parse(self, response):
        urls = response.xpath('//div[@class="states"]/ul/li/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
