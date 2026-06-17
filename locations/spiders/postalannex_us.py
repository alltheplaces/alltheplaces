import json

from scrapy import Selector, Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class PostalannexUSSpider(Spider):
    name = "postalannex_us"
    item_attributes = {"operator": "PostalAnnex", "operator_wikidata": "Q61960357"}
    start_urls = ["https://www.postalannex.com/locations"]

    def parse(self, response):
        script = response.xpath("//script[starts-with(text(), 'jQuery.extend')]/text()").get()
        for marker in json.loads(script[script.find("{") : script.rfind("}") + 1])["gmap"]["auto1map"]["markers"]:
            selector = Selector(text=marker["text"])

            item = Feature()
            item["lat"] = marker["latitude"]
            item["lon"] = marker["longitude"]
            item["website"] = response.urljoin(selector.css(".views-field-field-store-name a::attr(href)").get())
            item["branch"] = selector.css(".views-field-field-store-name a::text").get()
            if name := selector.xpath("//span[@itemprop='name']/text()").get():
                item["ref"] = name[name.find("#") + 1 :].strip().removesuffix(" - COMING SOON")
            else:
                item["ref"] = item["website"].split("/")[-1]
            item["street_address"] = selector.xpath("//span[@itemprop='streetAddress']/text()").get()
            item["postcode"] = selector.xpath("//span[@itemprop='postalCode']/text()").get()
            item["city"] = selector.xpath("//span[@itemprop='addressLocality']/text()").get()
            item["state"] = selector.xpath("//span[@itemprop='addressRegion']/text()").get()
            item["phone"] = selector.css(".views-field-field-phone .field-content::text").get()

            apply_category(Categories.POST_OFFICE, item)

            yield item
