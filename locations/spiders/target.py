import json
import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem
from scrapy.selector import Selector


class TargetSpider(scrapy.Spider):
    name = "target"
    item_attributes = {"brand": "Target", "brand_wikidata": "Q1046951"}
    allowed_domains = ["target.com"]
    start_urls = (
        # stores seem to have their own site index taken from
        # https://www.target.com/sitemap_index.xml.gz
        "https://www.target.com/sl/sitemap_001.xml.gz",
    )

    def parse(self, response):
        xml = Selector(response)
        xml.remove_namespaces()

        urls = xml.xpath("//loc/text()").extract()
        for url in urls:
            yield scrapy.Request(url, callback=self.parse_store)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            try:
                opening_hours.add_range(
                    day=hour["dayOfWeek"].replace("http://schema.org/", "")[:2],
                    open_time=hour["opens"],
                    close_time=hour["closes"],
                    time_format="%H:%M:%S",
                )
            except:
                continue  # closed or no time range given
        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        data = response.xpath('//script[@type="application/ld+json"]/text()').re_first(
            ".*"
        )
        if data:
            data = json.loads(data)
        else:
            return

        properties = {
            "ref": response.url.split("/")[-1],
            "name": data["name"],
            "addr_full": data["address"]["streetAddress"].strip(),
            "city": data["address"]["addressLocality"].strip(),
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": data["address"].get("addressCountry"),
            "phone": data.get("telephone"),
            "lat": float(data["geo"]["latitude"]),
            "lon": float(data["geo"]["longitude"]),
            "website": data.get("url") or response.url,
        }

        hours = self.parse_hours(data["openingHoursSpecification"])
        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)
