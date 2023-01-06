from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class SixtSpider(SitemapSpider, StructuredDataSpider):
    name = "sixt"
    item_attributes = {"brand": "SIXT", "brand_wikidata": "Q705664"}
    sitemap_urls = ["https://www.sixt.co.uk/car-hire/xml-sitemaps/branches.xml"]
    sitemap_rules = [(r"\/car-hire\/[-\w]+\/[-\w]+\/[-\w]+\/$", "parse_sd")]

    def pre_process_data(self, ld_data, **kwargs):
        if not ld_data["address"].get("addressCountry"):
            ld_data["address"]["addressCountry"] = ld_data["address"].pop("addressRegion")
