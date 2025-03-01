import json

from scrapy import Selector, Spider

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class PostalannexUSSpider(Spider):
    name = "postalannex_us"
    item_attributes = {"operator": "PostalAnnex", "operator_wikidata": "Q61960357"}
    start_urls = ["https://www.postalannex.com/location-results"]

    def parse(self, response):
        script = response.xpath("//script[starts-with(text(), 'jQuery.extend')]/text()").get()
        for marker in json.loads(script[script.find("{") : script.rfind("}") + 1])["gmap"]["auto1map"]["markers"]:
            selector = Selector(text=marker["text"])
            MicrodataParser.convert_to_json_ld(selector)
            item = LinkedDataParser.parse_ld(
                {
                    "geo": {
                        "@type": "GeoCoordinates",
                        "latitude": marker["latitude"],
                        "longitude": marker["longitude"],
                    },
                    "url": response.urljoin(selector.css(".views-field-field-store-name a::attr(href)").get()),
                    "address": list(LinkedDataParser.iter_linked_data(selector)),
                    "telephone": selector.css(".views-field-field-phone .field-content::text").get(),
                }
            )
            item["branch"] = selector.css(".views-field-field-store-name a::text").get()
            item["ref"] = item["website"].split("/")[-1]

            apply_category(Categories.POST_OFFICE, item)

            yield item
