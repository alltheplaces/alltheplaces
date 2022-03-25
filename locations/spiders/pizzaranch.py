import scrapy
import re
from locations.items import GeojsonPointItem
import json


class CVSSpider(scrapy.Spider):

    name = "pizzaranch"
    item_attributes = {"brand": "Pizza Ranch"}
    allowed_domains = ["pizzaranch.com"]
    download_delay = 0.5
    start_urls = ("https://pizzaranch.com/locations",)

    def parse_times(self, times):
        if times.strip() == "Open 24 hours":
            return "24/7"
        hours_to = [x.strip() for x in times.split("-")]
        cleaned_times = []

        for hour in hours_to:
            if re.search("PM$", hour):
                hour = re.sub("PM", "", hour).strip()
                hour_min = hour.split(":")
                if int(hour_min[0]) < 12:
                    hour_min[0] = str(12 + int(hour_min[0]))
                cleaned_times.append(":".join(hour_min))

            if re.search("AM$", hour):
                hour = re.sub("AM", "", hour).strip()
                hour_min = hour.split(":")
                if len(hour_min[0]) < 2:
                    hour_min[0] = hour_min[0].zfill(2)
                else:
                    hour_min[0] = str(int(hour_min[0]))

                cleaned_times.append(":".join(hour_min))
        return "-".join(cleaned_times)

    def parse_hours(self, lis):
        hours = []
        for li in lis:
            day = li.xpath(
                'normalize-space(.//td[@class="c-location-hours-details-row-day"]/text())'
            ).extract_first()[:2]
            times = li.xpath(
                './/td[@class="c-location-hours-details-row-intervals"]/span/span/text()'
            ).extract()
            times = "".join(x for x in times)
            if times and day:
                parsed_time = self.parse_times(times)
                hours.append(day + " " + parsed_time)

        return "; ".join(hours)

    def parse_stores(self, response):
        map_data = response.xpath(
            'normalize-space(//script[@id="js-map-config-dir-map-nap-map"]/text())'
        ).extract_first()
        map_json = json.loads(map_data)
        properties = {
            "name": response.xpath(
                '//span[@class="location-name-geo"]/text()'
            ).extract_first(),
            "addr_full": response.xpath(
                'normalize-space(//span[@itemprop="streetAddress"]/span/text())'
            ).extract_first(),
            "phone": response.xpath(
                'normalize-space(//div[@class="c-phone-number c-phone-main-number"]/span[@class="c-phone-number-span c-phone-main-number-span"]/text())'
            ).extract_first(),
            "city": response.xpath(
                'normalize-space(//span[@itemprop="addressLocality"]/text())'
            ).extract_first(),
            "state": response.xpath(
                'normalize-space(//abbr[@itemprop="addressRegion"]/text())'
            ).extract_first(),
            "postcode": response.xpath(
                'normalize-space(//span[@itemprop="postalCode"]/text())'
            ).extract_first(),
            "ref": map_json["locs"][0]["id"],
            "website": response.url,
            "lat": float(map_json["locs"][0]["latitude"]),
            "lon": float(map_json["locs"][0]["longitude"]),
        }
        hours = self.parse_hours(
            response.xpath(
                '//div[@class="hours-primary hidden-xs"]/div[@class="c-location-hours"]/div[@class="c-location-hours-details-wrapper js-location-hours"]/table/tbody/tr'
            )
        )

        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse_state_stores(self, response):
        stores = response.xpath('//h3[@class="title"]/a/@href').extract()
        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)

        next_page_url = response.xpath(
            '//div[@class="pagination"]//li[@class="next"]/a/@href'
        ).extract_first()

        if next_page_url:
            yield scrapy.Request(next_page_url, callback=self.parse_state_stores)

    def parse(self, response):
        urls = response.xpath('//ol[@class="state-list"]/li/a/@href').extract()
        for path in urls:
            yield scrapy.Request(
                response.urljoin(path), callback=self.parse_state_stores
            )
