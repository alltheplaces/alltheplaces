from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class JackInTheBoxSpider(SitemapSpider, StructuredDataSpider):
    name = "jack_in_the_box"
    item_attributes = {"brand": "Jack in the Box", "brand_wikidata": "Q1538507"}
    sitemap_urls = ["https://locations.jackinthebox.com/sitemap.xml"]
    sitemap_rules = [(r"com/\w\w/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    json_parser = "chompjs"
    time_format = "%I:%M %p"

    def pre_process_data(self, ld_data, **kwargs):
        for rule in ld_data.get("openingHoursSpecification", []):
            rule["opens"] = rule.get("opens", "").replace(".", "")
            rule["closes"] = rule.get("closes", "").replace(".", "")
