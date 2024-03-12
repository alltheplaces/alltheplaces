from scrapy.spiders import XMLFeedSpider

from locations.items import Feature


class BricoOKITSpider(XMLFeedSpider):
    name = "brico_ok_it"
    item_attributes = {"brand": "Brico OK", "brand_wikidata": "Q124719999"}
    start_urls = ["https://www.bricook.it/admin/bricook-store-locator/data.php"]

    def parse_node(self, response, selector):
        item = Feature()
        item["name"] = selector.xpath("location/text()").get()
        item["addr_full"] = selector.xpath("address/text()").get()
        item["lat"] = selector.xpath("latitude/text()").get()
        item["lon"] = selector.xpath("longitude/text()").get()
        item["email"] = selector.xpath("email/text()").get()
        item["ref"] = item["website"] = selector.xpath("exturl/text()").get()
        item["phone"] = selector.xpath("telephone/text()").get()
        item["image"] = selector.xpath("storeimage/text()").get()

        yield item
