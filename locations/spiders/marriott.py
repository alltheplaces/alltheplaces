import json
import re
import scrapy
from scrapy.selector import Selector


from locations.items import GeojsonPointItem


class MarriottHotels(scrapy.Spider):

    name = "marriott"
    allowed_domains = ["marriott.com", "ritzcarlton.com"]
    download_delay = 0.2

    def start_requests(self):
        start_urls = [
            (
                "http://www.ritzcarlton.com/en/hotels/map/_jcr_content/par_content/locationmap.PINS.html",
                self.parse_ritz,
            ),
            ("https://www.marriott.com/sitemap.us.hws.1.xml", self.parse),
        ]

        for url, callback in start_urls:
            yield scrapy.Request(url=url, callback=callback)

    def parse_hotel(self, response):
        if "invalidProperty=true" in response.url:
            return

        street_address = response.xpath(
            '//span[@itemprop="streetAddress"]/text()'
        ).extract_first()

        city = response.xpath(
            '//span[@itemprop="addressLocality"]/text()'
        ).extract_first()
        state = response.xpath(
            '//span[@itemprop="addressRegion"]/text()'
        ).extract_first()

        name = response.xpath(
            '//div[contains(@class, "m-hotel-info")]//span[@itemprop="name"]/text()'
        ).extract_first()
        if name:
            name = name.replace("\u2122", "")  # remove tm symbol

        brand = response.xpath(
            '//ul[contains(@class,"tile-breadcrumbs")]/li[2]/a/span/text()'
        ).extract_first()
        if brand == "Design HotelsTM":
            item_attributes = {"brand": "Design Hotels"}

        properties = {
            "ref": re.search(r".*/(.*)/$", response.url).groups()[0],
            "name": name,
            "addr_full": street_address,
            "city": city,
            "state": state,
            "postcode": response.xpath(
                '//span[@itemprop="postalCode"]/text()'
            ).extract_first(),
            "country": response.xpath(
                '//span[@itemprop="addressCountry"]/text()'
            ).extract_first(),
            "phone": (
                response.xpath('//span[@itemprop="telephone"]/text()').extract_first()
                or ""
            ).strip("| "),
            "lat": float(
                response.xpath('//span[@itemprop="latitude"]/text()').extract_first()
            ),
            "lon": float(
                response.xpath('//span[@itemprop="longitude"]/text()').extract_first()
            ),
            "website": response.url,
            "brand": brand,
        }

        yield GeojsonPointItem(**properties)

    def parse_ritz(self, response):
        brands = {
            "upcoming": "Ritz-Carlton",
            "reserve": "Ritz-Carton Reserve",
        }
        data = re.search(
            r"trc.pageProperties.trcMap.mapData= (.*)", response.text
        ).groups()[0]
        data = json.loads(data.strip(";\r\n "))

        for item in data["response"]["list"]["listItems"]["items"]:
            if item["venue"]["type"] in ("ritz", "upcoming"):
                name = "The Ritz-Carlton " + item["venue"]["name"]
            else:
                name = item["venue"]["name"]
            phone = re.split(r"<br./>", item["tip"]["text"])[-1]
            properties = {
                "ref": "-".join(
                    re.search(r".*/(.*)/(.*)$", item["tip"]["link"]["url"]).groups()
                ),
                "name": name,
                "addr_full": item["venue"]["location"]["address"].strip(),
                "city": item["venue"]["location"]["city"].strip(),
                "state": item["venue"]["location"]["state"].strip(),
                "postcode": item["venue"]["location"]["postalCode"].strip(". "),
                "country": item["venue"]["location"]["country"].strip(),
                "phone": phone.strip(),
                "lat": float(item["venue"]["location"]["lat"]),
                "lon": float(item["venue"]["location"]["lng"]),
                "website": item["tip"]["link"]["url"],
                "brand": brands.get(item["venue"]["type"], "Ritz-Carlton"),
            }

            yield GeojsonPointItem(**properties)

    def parse(self, response):
        xml = Selector(response)
        xml.remove_namespaces()

        urls = xml.xpath("//loc/text()").extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_hotel)
