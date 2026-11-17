import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class TorisenJPSpider(SitemapSpider):
    name = "torisen_jp"
    item_attributes = {"brand": "とりせん", "brand_wikidata": "Q11273505"}
    sitemap_urls = ["https://www.torisen.co.jp/shop-sitemap.xml"]

    def parse(self, response):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.xpath("//title/text()").get().split(" | ")[0].removesuffix("店")
        postcode, item["addr_full"] = response.xpath('//dt[text()="住所"]/following-sibling::dd/text()').getall()
        item["postcode"] = postcode.strip().removeprefix("〒")
        item["phone"] = response.xpath('//dt[text()="電話番号"]/following-sibling::dd/a/text()').get()
        item["image"] = response.css(".shop-info__image img::attr(src)").get()
        item["lon"], item["lat"] = re.search(
            r"!2d([\d.]+)!3d([\d.]+)", response.css(".shop-map iframe::attr(src)").get()
        ).groups()

        hours = response.xpath('//dt[text()="営業時間"]/following-sibling::dd/text()').get()
        (open_h, open_m), (close_h, close_m) = re.findall(r"(\d+)時(?:(\d+)分)?", hours)
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_days_range(DAYS, f"{open_h}:{open_m or '00'}", f"{close_h}:{close_m or '00'}")
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
