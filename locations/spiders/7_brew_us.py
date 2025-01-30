from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class SevenBrewUSSpider(SitemapSpider):
    name = "7_brew_us"
    allowed_domains = ["7brew.com"]
    start_urls = ["https://7brew.com"]
    item_attributes = {
        "brand": "7 Brew",
        "brand_wikidata": "Q127688691",
    }
    sitemap_urls = ["https://7brew.com/sitemap.xml"]
    sitemap_rules = [
        ("/location/", "parse"),
    ]

    def parse(self, response):
        item = Feature()
        item["name"] = response.xpath('//h1//text()').get()
        item["street_address"] = response.xpath('//h5//text()').get()
        item["addr_full"] = ",".join([item["street_address"],response.xpath('//em/text()').get()])
        item["ref"] = item["website"] = response.url
        item["opening_hours"] = OpeningHours()
        for day_time in response.xpath('//tbody/tr'):
            day = day_time.xpath('./td[1]/text()').get()
            open_time,close_time = day_time.xpath('./td[2]/text()').get().split('–')
            item["opening_hours"].add_range(day=day.strip(),open_time=open_time.strip(),close_time=close_time.strip(),time_format="%I:%M%p")
        apply_category(Categories.SHOP_COFFEE, item)
        yield item

