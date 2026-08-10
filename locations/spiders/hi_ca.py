import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class HiCASpider(SitemapSpider):
    name = "hi_ca"
    item_attributes = {
        "brand": "Hostelling International",
        "brand_wikidata": "Q16984941",
        "country": "CA",
    }
    sitemap_urls = ["https://hihostels.ca/en/sitemaps-1-section-hostels-1-sitemap.xml"]
    sitemap_rules = [("/en/destinations/", "parse")]

    def parse(self, response: Response, **kwargs):
        # Coordinates are in data-lat / data-lng on the map widget div
        lat = response.xpath("//*[@data-lat]/@data-lat").get()
        lng = response.xpath("//*[@data-lat]/@data-lng").get()
        if not lat or not lng:
            return

        # Name: first h2._title (h1._title is the booking widget heading)
        branch = response.css("h2._title::text").get()

        # Address block: "1114 Burnaby Street<br>Vancouver, British Columbia"
        addr_block = response.css("div._address").get("") or ""
        addr_lines = [
            re.sub(r"<[^>]+>", "", part).strip()
            for part in re.split(r"<br\s*/?>", addr_block)
            if re.sub(r"<[^>]+>", "", part).strip()
        ]
        street = addr_lines[0] if len(addr_lines) > 0 else None
        city = state = None
        if len(addr_lines) > 1:
            # e.g. "Vancouver, British Columbia"
            parts = addr_lines[1].split(",")
            city = parts[0].strip() if parts else None
            state = parts[1].strip() if len(parts) > 1 else None

        # Phone: first tel: href on the page
        phone = response.css("a[href^='tel:']::attr(href)").get()
        if phone:
            phone = phone.replace("tel:", "").strip()

        # Stable ref from URL slug
        ref = response.url.rstrip("/").rsplit("/", 1)[-1]

        item = Feature()
        item["ref"] = ref
        item["branch"] = branch
        item["lat"] = float(lat)
        item["lon"] = float(lng)
        item["street_address"] = street
        item["city"] = city
        item["state"] = state
        item["phone"] = phone
        item["website"] = response.url
        apply_category(Categories.TOURISM_HOSTEL, item)
        yield item
