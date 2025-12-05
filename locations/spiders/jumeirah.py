import json

from scrapy import Request

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class JumeirahSpider(StructuredDataSpider):
    name = "jumeirah"
    item_attributes = {"brand": "Jumeirah", "brand_wikidata": "Q1331200"}
    start_urls = ["https://www.jumeirah.com/en/stay"]

    def parse(self, response, **kwargs):
        data_json = json.loads(response.xpath('//script[@id="__JSS_STATE__"]/text()').get())
        for item in data_json["sitecore"]["route"]["placeholders"]["jss-main"]:
            if item.get("componentName") == "Hotelslist":
                if hotels := item.get("fields", {}).get("items", []):
                    for hotel in hotels:
                        yield Request(
                            url=response.urljoin(hotel.get("Hotel CTA Link").replace("\u002f", "/")),
                            callback=self.parse_sd,
                        )

    def post_process_item(self, item, response, ld_data):
        data_json = json.loads(response.xpath('//script[@id="__JSS_STATE__"]/text()').get())
        for piece in data_json["sitecore"]["route"]["placeholders"]["jss-main"]:
            if piece.get("componentName") == "ContactUsDetail":
                item["addr_full"] = piece.get("fields").get("Address Description", {}).get("value")
        item["branch"] = item.pop("name").replace("Jumeirah ", "")
        apply_category(Categories.HOTEL, item)
        yield item
