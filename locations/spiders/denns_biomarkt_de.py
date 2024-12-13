from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE, OpeningHours, sanitise_day
from locations.structured_data_spider import StructuredDataSpider


class DennsBiomarktDESpider(SitemapSpider, StructuredDataSpider):
    name = "denns_biomarkt_de"
    DENNS_BIO_MARKT = {"brand": "Denns BioMarkt", "brand_wikidata": "Q48883773"}
    sitemap_urls = ["https://www.biomarkt.de/robots.txt"]
    sitemap_rules = [(r"de/([^/]+)/marktseite$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item["name"].startswith("Denns BioMarkt"):
            item.update(self.DENNS_BIO_MARKT)

        apply_category(Categories.SHOP_SUPERMARKET, item)

        oh = OpeningHours()
        for dt in ld_data["openingHoursSpecification"]:
            for day in dt["dayOfWeek"]:
                if day := sanitise_day(day, DAYS_DE):
                    oh.add_range(day, dt["opens"], dt["closes"])
        item["opening_hours"] = oh
        yield item
