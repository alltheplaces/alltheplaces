import html
from datetime import datetime

from scrapy.spiders import SitemapSpider

from locations.hours import DAYS
from locations.structured_data_spider import StructuredDataSpider


class NettoSallingSpider(SitemapSpider, StructuredDataSpider):
    name = "netto_salling"
    item_attributes = {"brand": "Netto", "brand_wikidata": "Q552652"}
    sitemap_urls = [
        "https://www.netto.de/sitemap.xml",
        "https://www.netto.dk/sitemap.xml",
        "https://www.netto.pl/sitemap.xml",
    ]
    sitemap_rules = [
        ("/geschaefte/", "parse_sd"),
        ("/butikker/", "parse_sd"),
        ("/sklepy/", "parse_sd"),
    ]
    drop_attributes = {"image"}

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["name"] = html.unescape(ld_data["name"])
        ld_data["address"]["streetAddress"] = html.unescape(ld_data["address"]["streetAddress"])
        ld_data["address"]["addressLocality"] = html.unescape(ld_data["address"]["addressLocality"])

        for oh in ld_data.get("openingHoursSpecification", []):
            if oh.get("dayOfWeek"):
                continue
            if oh.get("validFrom", "") == oh.get("validThrough"):
                # No day, but we've got a day range of 1 day.
                oh["dayOfWeek"] = DAYS[datetime.strptime(oh["validFrom"], "%Y-%m-%d").weekday()]
