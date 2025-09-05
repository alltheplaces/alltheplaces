import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature


class BremerBankUSSpider(SitemapSpider):
    name = "bremer_bank_us"
    item_attributes = {"brand": "Bremer Bank", "brand_wikidata": "Q907603"}
    sitemap_urls = ["https://www.bremer.com/sitemap.xml"]
    sitemap_rules = [("/locations/", "parse")]
    custom_settings = {"DOWNLOAD_DELAY": 5}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        properties = {
            "ref": response.url.split("/")[-1],
            "street_address": response.xpath('//div[@class="col-sm-12 col-lg-4"]/div/p/text()').extract_first().strip(),
            "phone": response.xpath('//a[@class="phone-link"]/text()').extract_first(),
        }

        address_part2 = response.xpath('//div[@class="col-sm-12 col-lg-4"]/div/p/text()')[2].extract()
        match = re.match(r"^([^,]*),\s+(.*)\s+(\d{5})$", address_part2)
        (properties["city"], properties["state"], properties["postcode"]) = [m.strip() for m in match.groups()]

        extract_google_position(properties, response)

        apply_category(Categories.BANK, properties)

        yield Feature(**properties)
