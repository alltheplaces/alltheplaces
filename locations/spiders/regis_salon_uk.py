import scrapy
from locations.items import GeojsonPointItem
import re

regex_am = r"\s?([Aa][Mm])"
regex_pm = r"\s?([Pp][Mm])"


class RegisUKSpider(scrapy.Spider):
    name = "regis_uk"
    item_attributes = {"brand": "Regis Salon", "brand_wikidata": "Q110166032"}
    allowed_domains = ["www.regissalons.co.uk"]
    start_urls = ["https://www.regissalons.co.uk/salon-locator?show-all=yes"]
    download_delay = 4.0

    def convert_hours(self, hours):
        hours = [x.strip() for x in hours]
        hours = [x for x in hours if x]
        for i in range(len(hours)):
            converted_times = ""
            if hours[i] != "Closed":
                from_hr, to_hr = [hr.strip() for hr in hours[i].split("–")]
                if re.search(regex_am, from_hr):
                    from_hr = re.sub(regex_am, "", from_hr)
                    hour_min = re.split("[:.]", from_hr)
                    if len(hour_min[0]) < 2:
                        hour_min[0].zfill(2)
                    converted_times += (":".join(hour_min)) + " - "
                else:
                    from_hr = re.sub(regex_pm, "", from_hr)
                    hour_min = re.split("[:.]", from_hr)
                    if int(hour_min[0]) < 12:
                        hour_min[0] = str(12 + int(hour_min[0]))
                    converted_times += (":".join(hour_min)) + " - "

                if re.search(regex_am, to_hr):
                    to_hr = re.sub(regex_am, "", to_hr)
                    hour_min = re.split("[:.]", to_hr)
                    if len(hour_min[0]) < 2:
                        hour_min[0].zfill(2)
                    if int(hour_min[0]) == 12:
                        hour_min[0] = "00"
                    converted_times += ":".join(hour_min)
                else:
                    to_hr = re.sub(regex_pm, "", to_hr)
                    hour_min = re.split("[:.]", to_hr)
                    if int(hour_min[0]) < 12:
                        hour_min[0] = str(12 + int(hour_min[0]))
                    converted_times += ":".join(hour_min)
            else:
                converted_times += "off"
            hours[i] = converted_times
        days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        hours = "".join("{} {} ".format(*t) for t in zip(days, hours))
        return hours

    def parse_store(self, response):
        phone = (
            response.xpath('//a[@class="phone-tracked-link"]/text()')
            .extract_first()
            .strip()
        )
        lat = response.xpath('//div[@id="map-aside"]/@data-lat').extract_first()
        lon = response.xpath('//div[@id="map-aside"]/@data-lng').extract_first()
        hours = response.xpath(
            '//div[@class="container"]//p[contains(., "am")'
            ' or contains(., "Closed")]/text()'
        ).extract()
        hours = self.convert_hours(hours)

        yield GeojsonPointItem(
            ref=response.url,
            phone=phone,
            lat=lat,
            lon=lon,
            opening_hours=hours,
            website=response.url,
        )

    def parse(self, response):
        stores = response.xpath('//ul[@class="list"]//a/@href').extract()
        for store in stores:
            if "/salon-region/" in store:
                continue
            yield scrapy.Request(store, callback=self.parse_store)
