import itertools
import re

from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_DE, OpeningHours
from locations.items import Feature


class FustCHSpider(SitemapSpider):
    name = "fust_ch"
    item_attributes = {
        "brand": "Fust",
        "brand_wikidata": "Q1227164",
        "country": "CH",
    }
    allowed_domains = ["www.fust.ch"]
    sitemap_urls = ["https://www.fust.ch/sitemap.xml"]
    sitemap_follow = ["/myinterfaces", "/sitemap/www.fust.ch-de-"]
    sitemap_rules = [(r"/de/.+/filialen/", "parse")]

    def parse(self, response):
        # The site uses microformats, but it’s always for the headquarter,
        # not for the branch.
        email = self.parse_email(response)
        if not email:
            return
        s = response.css(".requestFiliale")
        branch = self.parse_branch(s)
        lat, lon = self.parse_lat_lon(s)
        properties = {
            "city": branch.split()[0],
            "branch": branch,
            "email": email,
            "image": self.parse_image(response),
            "lat": lat,
            "lon": lon,
            "opening_hours": self.parse_opening_hours(response),
            "phone": self.parse_phone(response),
            "postcode": s.xpath("@data-prj-zip").get(),
            "ref": email.split("@")[0],
            "street_address": s.xpath("@data-prj-adress").get(),
            "website": response.url,
        }
        yield Feature(**properties)

    def parse_branch(self, s):
        return s.xpath("@data-prj-city").get().split("(")[0].strip()

    def parse_email(self, s):
        if match := re.search(r"s?\d+@fust.ch", s.text):
            return match.group(0)

    def parse_image(self, s):
        url = s.css(".filialeimg").xpath("@data-src").get()
        return s.urljoin(url.split("?")[0]) if url else None

    def parse_lat_lon(self, s):
        map_url = s.xpath("//a[@data-fancy-wrapcss]/@href").get()
        if match := re.search(r"&ll=(\d+\.\d+),(\d+\.\d+)", map_url):
            lat, lon = map(float, match.groups())
            if lat != 0.0 and lon != 0.0:
                return (lat, lon)
        return (None, None)

    def parse_opening_hours(self, s):
        oh = OpeningHours()
        e = s.xpath("//div[text()='Öffnungszeiten']/../table/tr/td/text()")
        e = [x.strip() for x in e.getall() if x.strip()]
        for day, hours in itertools.pairwise(e):
            day = DAYS_DE.get(day)
            match = re.match(r"^(\d{2}:\d{2})-(\d{2}:\d{2})$", hours)
            if day and match:
                open_time, close_time = match.groups()
                oh.add_range(day, open_time, close_time)
        return oh.as_opening_hours()

    def parse_phone(self, response):
        for url in response.xpath("//div[text()='Kontakt']/..//a/@href").getall():
            url = url.strip()
            if url.startswith("tel:+41"):
                return url[4:]
