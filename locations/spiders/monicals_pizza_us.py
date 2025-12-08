from scrapy.spiders import SitemapSpider

from locations.items import Feature


# Only half the Microdata :(
class MonicalsPizzaUSSpider(SitemapSpider):
    name = "monicals_pizza_us"
    item_attributes = {"brand": "Monical's Pizza", "brand_wikidata": "Q6900121"}
    allowed_domains = ["www.monicals.com"]
    sitemap_urls = ["https://www.monicals.com/wp-sitemap.xml"]
    sitemap_follow = ["location"]
    sitemap_rules = [("/locations/", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["lat"] = response.xpath('//*[@id="location-lat"]/@value').get()
        item["lon"] = response.xpath('//*[@id="location-lng"]/@value').get()
        item["name"] = response.xpath('//div[@class="title-wrap"]/h2/text()').get()
        item["phone"] = response.xpath('//div[@class="phone"]/text()').get()
        item["street_address"] = response.xpath('//li[@itemprop="streetAddress"]/text()').get()
        item["city"] = response.xpath('//span[@itemprop="addressLocality"]/text()').get()
        item["state"] = response.xpath('//span[@itemprop="addressRegion"]/text()').get()
        item["postcode"] = response.xpath('//span[@itemprop="postalCode"]/text()').get()
        item["website"] = item["ref"] = response.url

        yield item
