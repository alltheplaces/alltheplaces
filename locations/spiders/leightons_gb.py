import html

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class LeightonsGBSpider(SitemapSpider, StructuredDataSpider):
    name = "leightons_gb"
    item_attributes = {"brand": "Leightons", "brand_wikidata": "Q117867339"}
    sitemap_urls = ["https://www.leightons.co.uk/sitemap.xml"]
    sitemap_rules = [(r"/branches/[-\w]+$", "parse_sd")]

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["name"] = html.unescape(ld_data["name"])
        for rule in ld_data["openingHoursSpecification"]:
            if "-" in rule["opens"]:
                rule["opens"], rule["closes"] = rule["opens"].split("-")
