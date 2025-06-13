from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address

# NOTE:
# All Noppes stores are now RataPlan locations.
# For reference: https://rataplan.nl/en/noppes-en-rataplan-nu-samen-de-grootste-kringloopketen-van-nederland/


class RataplanNLSpider(SitemapSpider):
    name = "rataplan_nl"
    item_attributes = {"brand": "RataPlan", "brand_wikidata": "Q100890251"}
    allowed_domains = ["rataplan.nl"]
    sitemap_urls = ["https://rataplan.nl/page-sitemap.xml"]
    sitemap_rules = [(r"rataplan\.nl/rataplan-kringloopwinkels/kringloopwinkel-rataplan-[-\w]+/?$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        address = response.xpath('//*[contains(text(),"Adresgegevens")]')
        if not address:  # closed location with no address info
            return
        item = Feature()
        item["ref"] = response.xpath("//@data-gt-widget-id").get()
        item["website"] = response.url
        item["addr_full"] = clean_address(
            response.xpath('//*[contains(text(),"Adresgegevens")]/following-sibling::p/text()').getall()[:2]
        )
        item["phone"] = response.xpath('//a[contains(@href, "tel:")]/@href').get()
        extract_google_position(item, response)
        item["name"] = self.item_attributes["brand"]

        apply_category(Categories.SHOP_SECOND_HAND, item)
        yield item
