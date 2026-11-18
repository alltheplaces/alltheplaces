import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_HR, DAYS_SI, OpeningHours, sanitise_day
from locations.structured_data_spider import StructuredDataSpider


class EurospinSpider(SitemapSpider, StructuredDataSpider):
    name = "eurospin"
    item_attributes = {"brand": "EuroSpin", "brand_wikidata": "Q1374674"}
    sitemap_urls = [
        "https://www.eurospin.com/it-it/sitemap-stores.xml",
        "https://www.eurospin.si/store-sitemap.xml",
        "https://www.eurospin.hr/store-sitemap.xml",
    ]
    sitemap_rules = [("/punti-vendita/|/prodajna-mesta/|/nase-poslovnice/", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["street_address"] = re.sub("(?sim)<.+?>", " ", str(item["street_address"]))
        item["branch"] = item.pop("name")
        item["ref"] = item["website"]
        item.pop("image", None)
        item.pop("phone")
        item.pop("email")
        if not item.get("opening_hours") and (days := {"HR": DAYS_HR, "SI": DAYS_SI}.get(item.get("country"))):
            item["opening_hours"] = self.parse_html_hours(response, days)
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item

    @staticmethod
    def parse_html_hours(response, days):
        heading = '//h2[contains(., "RADNO VRIJEME") or contains(., "URNIK")]'
        hours_text = " ".join(
            response.xpath(f"{heading}/following-sibling::text()|{heading}/following-sibling::strong/text()").getall()
        )
        oh = OpeningHours()
        for day, open_time, close_time, closed in re.findall(
            r"(\w+):\s*(?:(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})|(Zatvoreno|-))", hours_text
        ):
            if not (day := sanitise_day(day, days)):
                continue
            if closed:
                oh.set_closed(day)
            else:
                oh.add_range(day, open_time, close_time)
        return oh
