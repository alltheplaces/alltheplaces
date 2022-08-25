import json

from scrapy import Spider

from locations.items import GeojsonPointItem


class ChelmsfordStarCoopSpider(Spider):
    name = "chelmsford_star_coop"
    item_attributes = {
        "brand": "Chelmsford Star Coop",
        "brand_wikidata": "Q5089972",
        "country": "GB",
    }
    start_urls = ["https://www.chelmsfordstar.coop/find-us/"]

    def parse(self, response):
        script = response.xpath('//script[contains(., "var map5 =")]/text()').get()
        script = (
            script.replace("jQuery(document).ready(function($) {", "")
            .replace('var map5 = $("#map5").maps(', "")
            .replace(').data("wpgmp_maps");', "")
            .replace("});", "")
        )

        stores = json.loads(script)["places"]

        for store in stores:
            item = GeojsonPointItem()

            item["ref"] = store["id"]
            item["name"] = store["title"]
            item["addr_full"] = store["address"]
            item["lat"] = store["location"]["lat"]
            item["lon"] = store["location"]["lng"]
            item["website"] = store["location"]["redirect_permalink"]

            yield item
