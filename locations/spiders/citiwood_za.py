from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class CitiwoodZASpider(SitemapSpider):
    name = "citiwood_za"
    item_attributes = {
        "brand": "Citiwood",
        "brand_wikidata": "Q130407139",
    }
    allowed_domains = ["citiwood.co.za"]
    sitemap_urls = ["https://citiwood.co.za/store-locations-sitemap.xml"]
    sitemap_rules = [(r"/store-location/citiwood-[-\w+]", "parse")]

    def parse(self, response: Response) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = response.url.split("citiwood-")[-1].strip("/")
        item["branch"] = item["ref"].title()
        item["website"] = response.url
        item["addr_full"] = clean_address(response.xpath('//*[contains(@class, "address_physical")]//p/text()').get(""))
        item["phone"] = response.xpath(
            '//*[contains(@class, "contact_phone_office")]//a[contains(@href,"tel:")]/@href'
        ).get()
        apply_category(Categories.SHOP_TRADE, item)
        yield item
