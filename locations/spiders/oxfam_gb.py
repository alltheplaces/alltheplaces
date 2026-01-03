from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category, apply_yes_no
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.structured_data_spider import extract_email, extract_phone


class OxfamGBSpider(SitemapSpider):
    name = "oxfam_gb"
    item_attributes = {"brand": "Oxfam", "brand_wikidata": "Q267941"}
    sitemap_urls = ["https://www.oxfam.org.uk/sitemap.xml"]
    sitemap_rules = [("/shops/oxfam-", "parse_shop")]
    brands = {
        "oxfam-shop-": {"brand": "Oxfam", "brand_wikidata": "Q267941", "extras": Categories.SHOP_CHARITY.value},
        "oxfam-bookshop-": {"brand": "Oxfam Bookshop", "brand_wikidata": "Q7115196"},
        "oxfam-books-music-": {"brand": "Oxfam Books & Music", "brand_wikidata": "Q117838013"},
        # oxfam-boutique- (4)
        # oxfam-emporium- (1)
        # oxfam-festivals-shop (1)
        # oxfam-furniture-shop- (1)
        # oxfam-homeware- (2)
        # oxfam-music-audio- (1)
        # oxfam-music-shop- (4)
        # oxfam-online-hub- (2)
        # oxfam-original- (2)
        # oxfam-superstore- (1)
    }
    recycle_types = {
        "books": "recycling:books",
        # "boutique": "",
        # "bridal": "",
        "clothing": "recycling:clothes",
        "electricals": "recycling:electrical_appliances",
        # "ephemera": "",
        "furniture": "recycling:furniture",
        # "homewares": "",
        "music": "recycling:cds",
    }

    def parse_shop(self, response: TextResponse) -> Iterable[Feature]:
        item = Feature()
        item["website"] = item["ref"] = response.url
        item["name"] = response.xpath('normalize-space(//h1[@class="t t--h1  t--h1-pushed"]/text())').get()
        item["street_address"] = response.xpath('//*[@class="shop-address"]/li/text()').get()
        item["city"] = response.xpath('//*[@class="shop-address"]/li[2]/text()').get()
        item["postcode"] = response.xpath('//*[@class="shop-address"]/li[3]/text()').get()

        extract_google_position(item, response.selector)
        extract_email(item, response.selector)
        extract_phone(item, response.selector)

        for url, brand in self.brands.items():
            if url in response.url:
                item.update(brand)
                break
        else:
            apply_category(Categories.SHOP_CHARITY, item)

        for kind in response.xpath('//li[contains(@class, "shop-accepts__item")]/@class').getall():
            kind = kind.replace("shop-accepts__item", "").replace("--", "").strip()
            if tag := self.recycle_types.get(kind):
                apply_yes_no(tag, item, True)

        yield item
