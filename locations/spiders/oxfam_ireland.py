from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category, apply_yes_no
from locations.items import Feature


class OxfamIrelandSpider(SitemapSpider):
    name = "oxfam_ireland"
    item_attributes = {"brand": "Oxfam", "brand_wikidata": "Q267941"}
    sitemap_urls = ["https://www.oxfamireland.org/sitemap.xml"]
    sitemap_rules = [("/shops/", "parse")]
    recycle_types = {
        "accessories": None,
        "books": "recycling:books",
        "clothing": "recycling:clothes",
        "electricals": "recycling:electrical_appliances",
        "furniture": "recycling:furniture",
        "homewares": None,
        "music": None,
        "vintage": None,
    }

    def sitemap_filter(self, entries):
        for entry in entries:
            entry["loc"] = entry["loc"].replace("http://default", "https://www.oxfamireland.org")
            yield entry

    def parse(self, response, **kwargs):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["addr_full"] = response.xpath('//*[contains(@class, "address")]/text()').get()
        item["name"] = response.xpath('//meta[@property="og:title"]/@content').get()
        item["email"] = response.xpath('//a[contains(@href, "mailto")]/text()').get()
        item["phone"] = response.xpath('//a[contains(@href, "tel")]/text()').get()

        apply_category(Categories.SHOP_CHARITY, item)

        for label in response.xpath('//*[contains(@class, "shop-accepts-item-label")]/text()').getall():
            if tag := self.recycle_types.get(label.strip().lower()):
                apply_yes_no(tag, item, True)

        yield item
