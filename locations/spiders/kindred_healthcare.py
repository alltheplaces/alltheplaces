import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class KindredHealthcareSpider(SitemapSpider, StructuredDataSpider):
    name = "kindred_healthcare"
    item_attributes = {"brand": "Kindred Healthcare", "brand_wikidata": "Q921363"}
    allowed_domains = ["www.kindredhospitals.com"]
    sitemap_urls = [
        "https://www.kindredhospitals.com/sitemap/sitemap.xml",
    ]
    sitemap_rules = [(r"https://www.kindredhospitals.com/locations/ltac/[\w-]+/contact-us", "parse_sd")]
    wanted_types = ["Hospital"]

    def post_process_item(self, item, response, ld_data):
        facility_type = ld_data["@type"]
        if facility_type == "Hospital":  # Keep refs consistent
            ref = re.search(r".+/(.+?)/(.+?)/?(?:\.html|$)", response.url).group(1)
        else:
            ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)

        item["ref"] = ref

        yield item
