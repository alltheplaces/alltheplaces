import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_JP, DAYS_WEEKDAY, OpeningHours, sanitise_day
from locations.items import Feature


class MiraiyaShotenJPSpider(SitemapSpider):
    name = "miraiya_shoten_jp"
    item_attributes = {"brand": "未来屋書店", "brand_wikidata": "Q11519563"}
    sitemap_urls = ["https://www.miraiyashoten.co.jp/wp-sitemap-posts-shop-1.xml"]

    def parse(self, response):
        name = response.css("h4.midashi span::text").get()
        item = Feature()
        # The operator also runs a few shops under other names (ミライア and others).
        if name.startswith("アシーネ"):
            item["brand"], item["brand_wikidata"] = "アシーネ", "Q11283275"
            apply_category(Categories.SHOP_BOOKS, item)
        elif not name.startswith("未来屋書店"):
            return
        info = response.css("#shop_detail_info td.first")
        postcode, address = info[0].css("::text").getall()[:2]
        item["ref"] = item["website"] = response.url
        item["name"] = name
        item["postcode"] = postcode.strip().removeprefix("〒")
        item["addr_full"] = address
        item["phone"] = info[1].css("::text").get()
        item["lat"], item["lon"] = re.search(
            r"q=([-\d.]+),\s*([-\d.]+)", response.css("#gmap iframe::attr(src)").get()
        ).groups()

        oh = OpeningHours()
        for label in info[2].css("span.open_time"):
            day = label.css("::text").get()
            days = DAYS_WEEKDAY if day.startswith("平") else [sanitise_day(day[0], DAYS_JP)]
            if times := re.match(
                r"\s*(\d+:\d\d)～(\d+:\d\d)", label.xpath("following-sibling::text()[1]").get().replace("：", ":")
            ):
                oh.add_days_range(days, *times.groups())
        item["opening_hours"] = oh

        yield item
