from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class UnePieceEnPlusFRSpider(SitemapSpider):
    name = "une_piece_en_plus_fr"
    item_attributes = {"brand": "Une pièce en plus", "brand_wikidata": "Q130578849"}
    sitemap_urls = ["https://www.unepieceenplus.com/sitemap.xml"]
    sitemap_rules = [(r"/garde-meuble/[^/]+/$", "parse")]

    def parse(self, response, **kwargs):
        for card in response.xpath('//*[@itemtype="https://schema.org/SelfStorage"]'):
            link = card.xpath(".//a[@data-tracking-id]")
            item = Feature()
            item["ref"] = link.xpath("./@data-tracking-id").get()
            item["branch"] = link.xpath("normalize-space(.)").get()
            item["website"] = response.urljoin(link.xpath("./@href").get())
            item["addr_full"] = ", ".join(card.xpath('.//*[@itemprop="address"]//text()').getall())
            item["phone"] = card.xpath('.//meta[@itemprop="telephone"]/@content').get()
            item["lat"] = card.xpath('.//meta[@itemprop="latitude"]/@content').get()
            item["lon"] = card.xpath('.//meta[@itemprop="longitude"]/@content').get()
            apply_category(Categories.SHOP_STORAGE_RENTAL, item)
            yield item
