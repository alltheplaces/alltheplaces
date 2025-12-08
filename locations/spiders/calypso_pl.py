import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.pipelines.address_clean_up import clean_address
from locations.structured_data_spider import StructuredDataSpider


class CalypsoPLSpider(SitemapSpider, StructuredDataSpider):
    name = "calypso_pl"
    item_attributes = {"brand": "Calypso", "brand_wikidata": "Q126195554"}
    allowed_domains = ["calypso.com.pl"]
    sitemap_urls = ["https://www.calypso.com.pl/klub-sitemap.xml"]
    sitemap_rules = [("pl/en/klub/", "parse_sd")]

    def pre_process_data(self, ld_data, **kwargs):
        ld_hours = []
        for rule in ld_data.get("openingHours", []):
            rule = re.sub(r"([a-zA-Z])(\d+:\d+)", r"\1 \2", rule)
            ld_hours.extend(rule.split(", "))
        ld_data["openingHours"] = ld_hours

    def post_process_item(self, item, response, ld_data, **kwargs):
        # In few cases, ld_data have incomplete street_address
        item["street_address"] = clean_address(response.xpath('//*[@class="club-contact-info-cont"]/p/text()').get())
        apply_category(Categories.GYM, item)
        yield item
