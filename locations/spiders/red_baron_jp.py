import re

from scrapy.spiders import SitemapSpider

from locations.hours import DAYS, DAYS_JP, OpeningHours, sanitise_day
from locations.items import Feature


class RedBaronJPSpider(SitemapSpider):
    name = "red_baron_jp"
    item_attributes = {"brand": "レッドバロン", "brand_wikidata": "Q11349759"}
    sitemap_urls = ["https://www.redbaron.co.jp/shop-sitemap.xml"]
    sitemap_rules = [(r"/shop/.+\.html$", "parse")]

    def parse(self, response):
        name = response.css("h1.pageHeading-title span::text").get()
        # Skips a temporary page for the Suwa store (【仮店舗】) and a Yamaha dealership.
        if not name.startswith("レッドバロン"):
            return
        info = {
            row.xpath("normalize-space(th)").get(): row.xpath("normalize-space(td)").get()
            for row in response.css("table.l-sideTable tr")
        }
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = name.removeprefix("レッドバロン")
        item["postcode"], item["addr_full"] = info["住所"].removeprefix("〒").split(" ", 1)
        item["phone"] = info["電話番号"]
        item["lon"], item["lat"] = re.search(
            r"!2d([-\d.]+)!3d([-\d.]+)", response.css(".shopAccess iframe::attr(src)").get()
        ).groups()

        oh = OpeningHours()
        oh.add_days_range(DAYS, *re.match(r"(\d+:\d\d)~(\d+:\d\d)", info["営業時間"]).groups())
        if closed := sanitise_day(info["定休日"][0], DAYS_JP):
            oh.set_closed(closed)
        item["opening_hours"] = oh

        yield item
