import json

from scrapy.spiders import SitemapSpider

from locations.items import Feature


class PizzaExpressAESpider(SitemapSpider):
    name = "pizza_express_ae"
    item_attributes = {"brand": "PizzaExpress", "brand_wikidata": "Q662845"}
    sitemap_urls = ["https://www.pizzaexpress.ae/robots.txt"]
    sitemap_rules = [(r"/restaurants/([^/]+)$", "parse_store")]

    def parse_store(self, response, **kwargs):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["image"] = response.xpath('//meta[@itemprop="image"]/@content').get()
        item["phone"] = response.xpath('//span[@style="text-decoration:underline"]/text()').get()

        data = json.loads(response.xpath('//*[@class="sqs-block map-block sqs-block-map"]/@data-block-json').get())
        item["lat"] = data["location"]["markerLat"]
        item["lon"] = data["location"]["markerLng"]
        item["branch"] = data["location"]["addressTitle"].removeprefix("PizzaExpress ")

        yield item
