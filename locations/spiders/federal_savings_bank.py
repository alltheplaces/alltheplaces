import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class FederalSavingsBankSpider(SitemapSpider):
    name = "federal_savings_bank"
    item_attributes = {"brand": "Federal Savings Bank", "brand_wikidata": "Q116161036"}
    allowed_domains = ["thefederalsavingsbank.com"]
    sitemap_urls = ["https://www.thefederalsavingsbank.com/robots.txt"]
    sitemap_rules = [(r"location\/.*\/$", "parse_store")]

    def parse_store(self, response):
        info = response.xpath(
            '//div[@class="banner-content l-banner__col col-12 col-lg-7 order-2 order-lg-1"]/p[2]/text()'
        )

        intro_text = [line.extract().strip("\n") for line in info]
        if intro_text[0].startswith("("):
            intro_text = intro_text[1:]

        state_city = intro_text[1].split(", ")[1]
        properties = {
            "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
            "name": " ".join(response.xpath("//h1/text()").extract()),
            "street_address": intro_text[0],
            "city": intro_text[1].split(",")[0],
            "state": state_city.split(" ")[0],
            "postcode": state_city.split(" ")[1],
            "country": "US",
            "website": response.url,
        }
        try:
            properties["phone"] = intro_text[2]
        except IndexError:
            pass

        item = Feature(**properties)
        apply_category(Categories.OFFICE_FINANCIAL, item)

        yield item
