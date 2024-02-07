import re

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class BenchmarkHospitalitySpider(scrapy.Spider):
    name = "benchmark_hospitality"
    # item_attributes = {'brand': ''}   # doesn't really apply - Benchmark Hospitality is the operator or various
    # hotel franchise locations and other resort/meeting centers.
    allowed_domains = [
        "benchmarkglobalhospitality.com",
        "benchmarkresortsandhotels.com",
        "experiencebenchmark.com",
        "gemstonehotelcollection.com",
    ]
    start_urls = [
        "https://www.benchmarkglobalhospitality.com/property_locations/",
    ]

    def parse(self, response):
        point_script = " ".join(response.xpath('//script[contains(text(), "mapPointList")]/text()').extract())
        resorts = response.xpath('//li[contains(@class, "propertyName")]/a')

        for elem in resorts:
            name = elem.xpath("./text()").extract_first()
            href = elem.xpath("./@href").extract_first()
            lat, lon = re.search(name + r".*?coordinates:.lat:([\d\.\-]+),lng:([\d\.\-]+)", point_script).groups()

            properties = {"lat": float(lat), "lon": float(lon), "name": name}
            yield scrapy.Request(url=href, callback=self.parse_hotel, meta={"properties": properties})

    def parse_hotel(self, response):
        if "under_development" in response.url:
            return
        properties = response.meta["properties"]

        item = Feature()
        item["lat"] = properties["lat"]
        item["lon"] = properties["lon"]
        item["name"] = properties["name"]

        p = response.xpath('//p[@class="brand-cap"]/following-sibling::p/text()').extract_first()

        if p:
            p = p.replace(properties["name"], "").strip(" ,")
            address, phone = p.split(" P: ")
            phone = phone.split("Toll Free")[0]
        else:
            p = response.xpath('//div[@class="contact"]/p/text()').extract()
            address = p[0]
            phone = ""

        item["ref"] = re.search(r".com/+(?:meeting/+)?(.+?)//?", response.url + "/").group(1)
        item["addr_full"] = address.strip() if "Reservations" not in address else None
        item["phone"] = phone.strip()
        item["website"] = response.url

        if "Resort" in item["name"]:
            apply_category(Categories.LEISURE_RESORT, item)
        elif "Center" in item["name"]:
            apply_category({"amenity": "conference_centre"}, item)
        else:
            apply_category(Categories.HOTEL, item)

        yield item
