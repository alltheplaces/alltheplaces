import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class PetesMarketUSSpider(SitemapSpider):
    name = "petes_market_us"
    item_attributes = {"brand": "Pete's Market", "brand_wikidata": "Q118793358", "name": "Pete's Market"}
    sitemap_urls = ["https://www.petesfresh.com/sitemap.xml"]
    sitemap_rules = [(r"/stores/[^/]+$", "parse_store")]

    def parse_store(self, response):
        geo = response.css("div.geolocation-location")

        item = Feature()
        item["ref"] = response.url.rstrip("/").split("/")[-1]
        item["lat"] = geo.attrib.get("data-lat")
        item["lon"] = geo.attrib.get("data-lng")
        item["branch"] = response.css("h1.page-header span::text").get("").strip()
        item["website"] = response.url
        item["phone"] = response.css(".store-phone a::text").get()

        address_lines = [line.strip() for line in response.css(".store-address p::text").getall() if line.strip()]
        if len(address_lines) == 2:
            item["street_address"] = address_lines[0]
            if m := re.match(r"^(.*),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$", address_lines[1]):
                item["city"], item["state"], item["postcode"] = m.groups()
        item["country"] = "US"

        if m := re.search(r"(\d{1,2}:\d{2} [AP]M) - (\d{1,2}:\d{2} [AP]M) DAILY", response.css(".store-hours").get("")):
            oh = OpeningHours()
            oh.add_days_range(DAYS, m.group(1), m.group(2), time_format="%I:%M %p")
            item["opening_hours"] = oh

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
