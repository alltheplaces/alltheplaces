from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class KindredHealthcareSpider(SitemapSpider):
    name = "kindred_healthcare"
    item_attributes = {"brand": "Kindred Healthcare", "brand_wikidata": "Q921363", "country": "US"}
    sitemap_urls = [
        "https://www.kindredhospitals.com/sitemap.xml",
    ]
    sitemap_rules = [(r"https://www.kindredhospitals.com/locations/[a-z-0-9]+/[a-z-0-9]+$", "parse")]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["name"] = response.xpath("//h1/text()").get()
        item["addr_full"] = clean_address(response.xpath('//*[@class="cmp-text"]/p/text()').get())
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get().replace(".", "")
        item["ref"] = item["website"] = response.url
        extract_google_position(item, response)
        yield item
