import re

import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_DE, OpeningHours
from locations.items import Feature


# Technically, the site uses linked data, but in reality that contains only
# boilerplate. Anything interesting needs to be extracted from HTML.
class RotpunktApothekenCHSpider(scrapy.spiders.SitemapSpider):
    name = "rotpunkt_apotheken_ch"
    allowed_domains = ["www.rotpunkt-apotheken.ch"]
    sitemap_urls = ["https://www.rotpunkt-apotheken.ch/sitemaps-1-section-pharmaciesDetailPages-1-sitemap.xml"]

    def parse(self, response):
        props = {
            "email": self.parse_email(response),
            "extras": {
                "website": response.url,
            },
            "image": self.parse_image(response),
            "opening_hours": self.parse_opening_hours(response),
            "phone": self.parse_phone(response),
            "ref": response.url.split("/")[-1],
        }
        props.update(self.parse_addr(response))
        props.update(self.parse_lat_lon(response))
        props.update(self.parse_name(response, props["city"]))
        feature = Feature(**props)
        apply_category(Categories.PHARMACY, feature)
        apply_yes_no(Extras.WHEELCHAIR, feature, "Behindertengerechter Zugang" in response.text)
        yield feature

    def parse_addr(self, response):
        lines = response.xpath("//address/text()").getall()
        lines = [" ".join(line.split()) for line in lines]
        [street, housenumber] = lines[0].rsplit(" ", 1)
        [postcode, city] = lines[1].split(" ", 1)
        return {
            "brand": "Rotpunkt Apotheke",
            "brand_wikidata": "Q111683777",
            "city": city,
            "country": "CH",
            "housenumber": housenumber,
            "postcode": postcode,
            "street": street,
        }

    def parse_email(self, response):
        if match := re.search(r"mailto:([a-zA-Z0-9@.\-_]+)", response.text):
            return match.group(1)

    def parse_image(self, response):
        image = response.xpath('//meta[@property="og:image"]/@content').get()
        if image:
            return image.split("?")[0]

    def parse_lat_lon(self, response):
        url = re.search(r'(https://api.mapbox.com/[^"]+)', response.text).group(0)
        lon, lat = re.search(r"\(([\d.]+),([\d.]+)\)", url).groups()
        return {"lat": float(lat), "lon": float(lon)}

    def parse_name(self, response, city):
        title = response.xpath("//title/text()").get()
        name = " ".join(title.split("|")[0].split())
        return {"name": name.removesuffix(" " + city)}

    def parse_opening_hours(self, response):
        hours_list = response.css(".location-info__opening-hours-list")
        oh = OpeningHours()
        day = None
        for t in hours_list.xpath("*/text()").extract():
            day = DAYS_DE.get(t.strip(), day)
            for open_h, close_h in re.findall(r"(\d\d:\d\d) – (\d\d:\d\d)", t):
                oh.add_range(day, open_h, close_h)
        return oh.as_opening_hours()

    def parse_phone(self, response):
        if match := re.search(r'"tel:([\d\s]+)"', response.text):
            return match.group(1)

    def parse_website(self, response):
        links = [link for link in response.css(".text-link").xpath("@href").getall() if link.startswith("http")]
        return links[1]
