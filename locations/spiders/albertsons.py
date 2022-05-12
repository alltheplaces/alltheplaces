import re
import json

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class AlbertsonsSpider(scrapy.Spider):

    name = "albertsons"
    item_attributes = {"brand": "Albertsons", "brand_wikidata": "Q2831861"}
    download_delay = 0.5

    allowed_domains = [
        "local.albertsons.com",
        "local.acmemarkets.com",
        "local.albertsonsmarket.com",
        "local.amigosunited.com",
        "local.andronicos.com",
        "local.carrsqc.com",
        "local.jewelosco.com",
        "local.kingsfoodmarkets.com",
        "local.luckylowprices.com",
        "local.marketstreetunited.com",
        "local.pavilions.com",
        "local.randalls.com",
        "local.shaws.com",
        "local.starmarket.com",
        "local.tomthumb.com",
        "local.unitedsupermarkets.com",
        "local.vons.com",
    ]

    start_urls = [f"https://{domain}" for domain in allowed_domains]

    def parse_stores(self, response):
        js = json.loads(
            response.xpath('//script[contains(., "Yext.Profile")]/text()')
            .extract_first()
            .replace("window.Yext = (function(Yext){Yext.Profile = ", "")
            .replace("; return Yext;})(window.Yext || {});", "")
        )

        hours = OpeningHours()
        for day_spec in js["hours"]["normalHours"]:
            day = day_spec["day"][:2].capitalize()
            for interval in day_spec["intervals"]:
                open_hour, open_minute = divmod(interval["start"], 100)
                close_hour, close_minute = divmod(interval["end"], 100)
                open_time = f"{open_hour:02}:{open_minute:02}"
                close_time = f"{close_hour:02}:{close_minute:02}"
                hours.add_range(day, open_time, close_time)

        properties = {
            "addr_full": js["address"]["line1"],
            "extras": {
                "addr:unit": js["address"]["line2"],
                "loc_name": js["address"]["extraDescription"],
            },
            "phone": js["mainPhone"]["number"],
            "city": js["address"]["city"],
            "state": js["address"]["region"],
            "postcode": js["address"]["postalCode"],
            "name": js["name"],
            "ref": js["meta"]["id"],
            "website": response.url,
            "lat": js["yextDisplayCoordinate"]["lat"],
            "lon": js["yextDisplayCoordinate"]["long"],
            "brand": js["c_groceryBrand"],
            "opening_hours": hours.as_opening_hours(),
        }
        yield GeojsonPointItem(**properties)

    def parse_city_stores(self, response):
        stores = response.xpath(
            '//div[@class="Directory-content"]//h2/a/@href'
        ).extract()
        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)

    def parse_state(self, response):
        urls = response.xpath(
            '//div[@class="Directory-content"]/ul/li/a/@href'
        ).extract()
        for path in urls:
            pattern = re.compile(r"^[a-z]{2}\/[^()]+\/[^()]+.html$")
            if pattern.match(path.strip()):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
            else:
                yield scrapy.Request(
                    response.urljoin(path), callback=self.parse_city_stores
                )

    def parse(self, response):
        urls = response.xpath(
            '//div[@class="Directory-content"]/ul/li/a/@href'
        ).extract()
        for path in urls:
            pattern = re.compile("^[a-z]{2}.html$")
            pattern1 = re.compile(r"^[a-z]{2}\/[^()]+\/[^()]+.html$")
            if pattern.match(path.strip()):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
            elif pattern1.match(path.strip()):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
            else:
                yield scrapy.Request(
                    response.urljoin(path), callback=self.parse_city_stores
                )
