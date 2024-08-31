from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_CZ, OpeningHours, sanitise_day
from locations.items import Feature


class TetaCZSpider(SitemapSpider):
    name = "teta_cz"
    item_attributes = {"brand": "Teta", "brand_wikidata": "Q20860823"}
    sitemap_urls = ["https://www.tetadrogerie.cz/sitemap"]
    sitemap_rules = [(r"/prodejny/", "parse")]

    def parse(self, response, **kwargs):
        result = response
        item = Feature()
        item["lat"] = result.xpath("//*[@class = 'j-map-center-lat']/@value").get()
        item["lon"] = result.xpath("//*[@class = 'j-map-center-lng']/@value").get()
        item["phone"] = result.xpath("//*[@class = 'sx-store-detail-phone']//strong/text()").get()
        item["email"] = result.xpath("//*[@class = 'sx-store-detail-email']/text()").get()
        item["website"] = item["ref"] = response.url
        item["addr_full"] = result.xpath("//*[@class = 'CMSBreadCrumbsCurrentItem']/text()").get().strip()
        oh = OpeningHours()

        for rule in response.xpath(r'//*[@class = "sx-store-detail-opening-table"]//tr'):
            day = sanitise_day(rule.xpath(r"./td[1]/text()").get(), DAYS_CZ)
            time = rule.xpath(r"./td[2]/text()").get()

            if (time == "Zavřeno") or (day is None):
                continue

            for period in time.split(","):
                open_time, close_time = period.split("-")
                oh.add_range(day, open_time.strip(), close_time.strip())

        item["opening_hours"] = oh

        yield item
