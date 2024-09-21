from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class ErieInsuranceSpider(SitemapSpider, StructuredDataSpider):
    name = "erie_insurance"
    item_attributes = {
        "brand": "Erie Insurance",
        "brand_wikidata": "Q5388314",
        "country": "US",
    }
    allowed_domains = ["www.erieinsurance.com"]
    sitemap_urls = ["https://www.erieinsurance.com/sitemap.xml"]
    sitemap_rules = [(r"^https://www.erieinsurance.com/agencies/.", "parse_sd")]
    wanted_types = ["InsuranceAgency"]
