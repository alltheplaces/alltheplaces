from scrapy.spiders import SitemapSpider

from locations.storefinders.location_bank import Feature, OpeningHours


class LeightonsGBSpider(SitemapSpider):
    name = "leightons_gb"
    item_attributes = {"brand": "Leightons", "brand_wikidata": "Q117867339"}
    sitemap_urls = ["https://www.leightons.co.uk/sitemap.xml"]
    sitemap_rules = [(r"/pages/[-\w]+-opticians-audiologists$", "parse")]

    def parse(self, response):
        if response.xpath("//@data-branch-latitude").get():
            item = Feature()
            item["branch"] = response.xpath("//h1/text()").get()
            item["addr_full"] = response.xpath('//*[@class="address-line"]//text()').get()
            item["email"] = response.xpath('//*[contains(@href,"mailto")]/text()').get()
            item["phone"] = response.xpath('//*[contains(@href,"tel")]/text()').get()
            item["lat"] = response.xpath("//@data-branch-latitude").get()
            item["lon"] = response.xpath("//@data-branch-longitude").get()
            item["ref"] = item["website"] = response.url
            oh = OpeningHours()
            for day_time in response.xpath('//*[@class="opening-hours"]//li'):
                day = day_time.xpath(".//span[1]/text()").get()
                time = day_time.xpath(".//span[2]/text()").get()
                if time.lower() == "closed":
                    oh.set_closed(day)
                else:
                    open_time, close_time = time.split("-")
                    oh.add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip())
            item["opening_hours"] = oh
            yield item
