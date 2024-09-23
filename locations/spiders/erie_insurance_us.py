from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class ErieInsuranceUSSpider(SitemapSpider, StructuredDataSpider):
    name = "erie_insurance_us"
    item_attributes = {
        "brand": "Erie Insurance",
        "brand_wikidata": "Q5388314",
    }
    allowed_domains = ["www.erieinsurance.com"]
    sitemap_urls = ["https://www.erieinsurance.com/sitemap.xml"]
    sitemap_rules = [(r"^https://www.erieinsurance.com/agencies/.", "parse_sd")]
    wanted_types = ["InsuranceAgency"]
