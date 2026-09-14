import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT

LASER_CLINICS_SHARED_ATTRIBUTES = {"brand": "Laser Clinics", "brand_wikidata": "Q126539797"}

# Page coordinates are only available inside a Next.js RSC flight chunk, as a
# JSON string escaped within a <script> tag, e.g. \"center\":{\"lat\":1,\"lng\":2}
COORDS_RE = re.compile(r'\\"center\\":\{\\"lat\\":(-?[\d.]+),\\"lng\\":(-?[\d.]+)\}')


class LaserClinicsSpider(SitemapSpider):
    item_attributes = LASER_CLINICS_SHARED_ATTRIBUTES
    sitemap_rules = [(r"/skin-care-clinics?/[^/]+/?$", "parse")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT, "ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        if "closed-clinic" in response.url:
            return

        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["website"] = response.url

        h1 = response.xpath("//h1/text()").get("")
        item["branch"] = h1.rsplit(" - ", 1)[-1].strip() if " - " in h1 else h1.strip()

        item["addr_full"] = response.xpath(
            '//div[@id="clinic-location"]//h5[text()="Address"]/following-sibling::p[1]/text()'
        ).get()

        if phone := response.xpath(
            '//div[@id="clinic-location"]//h5[text()="Call us"]/following-sibling::p[1]/text()'
        ).get():
            item["phone"] = phone.replace("Ph:", "").strip()

        if m := COORDS_RE.search(response.text):
            item["lat"], item["lon"] = m.group(1), m.group(2)

        oh = OpeningHours()
        days = response.xpath('//div[@id="clinic-location"]//ul/li/span[1]/text()').getall()
        hours = response.xpath('//div[@id="clinic-location"]//ul/li/span[2]/text()').getall()
        for day, time_range in zip(days, hours):
            oh.add_ranges_from_string(f"{day}: {time_range}")
        item["opening_hours"] = oh

        apply_category(Categories.SHOP_BEAUTY_LASER_HAIR_REMOVAL, item)
        yield item


class LaserClinicsAUSpider(LaserClinicsSpider):
    name = "laser_clinics_au"
    item_attributes = {**LASER_CLINICS_SHARED_ATTRIBUTES, "country": "AU"}
    allowed_domains = ["www.laserclinics.com.au"]
    sitemap_urls = ["https://www.laserclinics.com.au/sitemap.xml"]
    requires_proxy = "AU"  # Vercel security checkpoint blocks datacentre IPs
