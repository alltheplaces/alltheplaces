from scrapy.spiders import SitemapSpider

from locations.items import Feature


class KutchenhausGBSpider(SitemapSpider):
    name = "kutchenhaus_gb"
    item_attributes = {"brand": "Kutchenhaus", "brand_wikidata": "Q123029245"}
    sitemap_urls = ["https://uk.kutchenhaus.com/sitemap.xml"]
    sitemap_follow = ["Store"]
    sitemap_rules = [(r"https:\/\/uk\.kutchenhaus\.com\/store-finder\/[-\w]+$", "parse")]
    custom_settings = {"REDIRECT_ENABLED": False}

    def parse(self, response, **kwargs):
        if label := response.xpath('//div[@class="store-details--label"]/text()').get():
            if label.strip() == "COMING SOON":
                return

        item = Feature()

        item["lat"] = response.xpath('//div[@id="storeDetailsMap"]/@data-store-geopoint-latitude').get()
        item["lon"] = response.xpath('//div[@id="storeDetailsMap"]/@data-store-geopoint-longitude').get()
        item["name"] = response.xpath('//div[@class="store-details--caption"]/h1/text()').get()
        item["addr_full"] = response.xpath('//div[@class="store-details--info-item col-10"]/text()').getall()[0].strip()
        item["phone"] = response.xpath('//div[@class="store-details--info-item col-10"]/a/text()').get()
        item["ref"] = item["website"] = response.url

        return item
