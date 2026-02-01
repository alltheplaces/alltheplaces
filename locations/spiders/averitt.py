import scrapy

from locations.google_url import extract_google_position
from locations.items import Feature


class AverittSpider(scrapy.spiders.SitemapSpider):
    name = "averitt"
    item_attributes = {"brand": "Averitt Express", "brand_wikidata": "Q4828320"}
    allowed_domains = ["averitt.com"]
    sitemap_urls = ["https://www.averitt.com/sitemap.xml"]
    sitemap_rules = [
        (r"^https://www.averitt.com/locations/[^/]+/[^/]", "parse"),
    ]

    def parse(self, response):
        # 1
        address_full = response.xpath(
            "/html/body/div[2]/div/div[1]/div/div/span/div[4]/div/div/div/div[2]/div/div/p[1]/span[1]/text()"
        ).get()
        city = response.xpath(
            "/html/body/div[2]/div/div[1]/div/div/span/div[4]/div/div/div/div[2]/div/div/p[1]/span[3]/text()"
        ).get()
        state = response.xpath(
            "/html/body/div[2]/div/div[1]/div/div/span/div[4]/div/div/div/div[2]/div/div/p[1]/span[5]/text()"
        ).get()
        postcode = response.xpath(
            "/html/body/div[2]/div/div[1]/div/div/span/div[4]/div/div/div/div[2]/div/div/p[1]/span[7]/text()"
        ).get()

        # 2
        if city is None:
            address_full = response.xpath(
                "/html/body/div[2]/div/div[1]/div/div/span/div[4]/div/div/div/div[2]/div/div/p[1]/span[2]/text()"
            ).get()
            city_state_postcode = response.xpath(
                "/html/body/div[2]/div/div[1]/div/div/span/div[4]/div/div/div/div[2]/div/div/p[1]/span[2]/text()"
            ).get()
            if address_full is not None:
                postcode = city_state_postcode.split()[-1]
                state = city_state_postcode.split()[-2]
                city = " ".join(city_state_postcode.split()[:-2]).replace(",", "")

        # 3
        if city is None:
            address_full = response.xpath(
                "/html/body/div[2]/div/div[1]/div/div/span/div[4]/div/div/div/div[2]/div/div/p/text()"
            ).get()
            address = response.xpath(
                "string(/html/body/div[2]/div/div[1]/div/div/span/div[4]/div/div/div/div[2]/div/div/p)"
            ).get()
            if address_full:
                city_state_postcode = address.replace(address_full, "")
                postcode = city_state_postcode.split()[-1]
                state = city_state_postcode.split()[-2]
                city = " ".join(city_state_postcode.split()[:-2]).replace(",", "")

        # 4
        if city is None:
            address_full = response.xpath(
                "/html/body/div[2]/div/div[1]/div/div/span/div[4]/div/div/div/div[2]/div/div/p[1]/span/text()"
            ).get()
            address = response.xpath(
                "string(/html/body/div[2]/div/div[1]/div/div/span/div[4]/div/div/div/div[2]/div/div/p[1]/span)"
            ).get()
            if address_full:
                city_state_postcode = address.replace(address_full, "")
                postcode = city_state_postcode.split()[-1]
                state = city_state_postcode.split()[-2]
                city = " ".join(city_state_postcode.split()[:-2]).replace(",", "")

        phone = response.xpath(
            "/html/body/div[2]/div/div[1]/div/div/span/div[2]/div/div/div/div[1]/div/div/p/a/text()"
        ).get()
        name = response.xpath(
            "/html/body/div[2]/div/div[1]/div/div/span/div[4]/div/div/div/div[2]/div/div/h3/strong/text()"
        ).get()
        properties = {
            "ref": response.url,
            "name": name,
            "street_address": address_full,
            "city": city,
            "state": state,
            "postcode": postcode,
            "phone": phone,
            "website": response.url,
        }
        extract_google_position(properties, response)

        yield Feature(**properties)
