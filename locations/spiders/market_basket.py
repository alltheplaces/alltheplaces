import re

import scrapy

from locations.items import Feature


class MarketBasketSpider(scrapy.Spider):
    name = "market_basket"
    item_attributes = {"brand": "Market Basket", "brand_wikidata": "Q6770657"}
    allowed_domains = ["www.mydemoulas.net"]
    download_delay = 0.5
    start_urls = ("http://www.mydemoulas.net/locations/",)

    def parse_times(self, times):
        if times.strip() == "Open 24 hours":
            return "24/7"
        hours_to = [x.strip() for x in times.split("-")]
        cleaned_times = []

        for hour in hours_to:
            if re.search("pm$", hour):
                hour = re.sub("pm", "", hour).strip()
                hour_min = hour.split(":")
                if int(hour_min[0]) < 12:
                    hour_min[0] = str(12 + int(hour_min[0]))
                cleaned_times.append(":".join(hour_min))

            if re.search("am$", hour):
                hour = re.sub("am", "", hour).strip()
                hour_min = hour.split(":")
                if len(hour_min[0]) < 2:
                    hour_min[0] = hour_min[0].zfill(2)
                else:
                    hour_min[0] = str(12 + int(hour_min[0]))

                cleaned_times.append(":".join(hour_min))
        return "-".join(cleaned_times)

    def parse_hours(self, lis):
        hours = []
        for li in lis:
            day = li.xpath("normalize-space(./strong/text())").extract_first()
            times = li.xpath("normalize-space(./text())").extract_first()
            if times and day:
                parsed_time = self.parse_times(times)
                hours.append(day[:2] + " " + parsed_time)

        return "; ".join(hours)

    def parse_stores(self, response):
        map_data = re.findall(r"pois\":\[{\"point\":{\"lat\":[^}]+", response.text)
        if len(map_data) == 0:
            return
        location = re.findall(r"[-.0-9]+", map_data[0])
        address = response.xpath(
            'normalize-space(//div[@itemtype="http://schema.org/Place"]/div[1]/p[contains(text() ,"Address:")]/text())'
        ).extract_first()
        address = address.replace("Address: ", "")
        if address == "":
            addr_full = ""
            state = ""
            city = ""
            postcode = ""
        else:
            addr_full = address.split(",")[0]
            postcode = re.findall(r"[0-9]+$", address.replace(addr_full, ""))[0]
            state = re.findall(r"[A-Z]{2}", address.replace(addr_full, ""))[0]
            city = re.findall(r"[A-Z][a-z]+", address.replace(addr_full, ""))
            if len(city) > 0:
                city = city[0]
            else:
                city = ""
        properties = {
            "addr_full": addr_full,
            "phone": response.xpath('normalize-space(//span[@itemprop="telephone"]/text())').extract_first(),
            "city": city,
            "state": state,
            "postcode": postcode,
            "ref": response.url,
            "website": response.url,
            "lat": float(location[0]),
            "lon": float(location[1]),
        }
        hours = self.parse_hours(response.xpath('//div[@class="textwidget custom-html-widget"]/ul/li'))
        if hours:
            properties["opening_hours"] = hours

        yield Feature(**properties)

    def parse_area(self, response):
        city_urls = response.xpath("//ol/li/a/@href|//ul/li/a/@href").extract()
        for path in city_urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)

    def parse(self, response):
        urls = response.xpath('//div[@class="cs-block-buton"]/a[@class="cs-button-links"]/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_area)
