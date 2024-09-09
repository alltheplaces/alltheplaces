import chompjs
from scrapy import Selector

from locations.json_blob_spider import JSONBlobSpider


class AlaskaCommercialCompanySpider(JSONBlobSpider):
    name = "alaska_commercial_company"
    item_attributes = {"brand": "Alaska Commercial Company", "brand_wikidata": "Q2637066"}
    allowed_domains = ["www.alaskacommercial.com"]
    start_urls = ("https://www.alaskacommercial.com/store-locator",)

    def extract_json(self, response):
        data = response.xpath('//script[contains(text(), "var locations = ")]/text()').get()
        return chompjs.parse_js_object(data)

    def pre_process_data(self, location):
        # {'pid': '143', 'title': 'Yakutat', 'details': '\n\t\t\t\t\t\t<h4>Yakutat <span>Alaska Commercial Company</span></h4>\n\t\t\t\t\t\t<p class="address"><strong>716 Ocean Cape Road<br />\n\t\t\t\t\t\t\tYakutat, Alaska<br />\n\t\t\t\t\t\t\t99689</strong>\n\t\t\t\t\t\t\t<br />Phone: 907-784-3386\n\t\t\t\t\t\t\t\n\t\t\t\t\t\t\t\n\t\t\t\t\t\t\t\n\t\t\t\t\t\t</p>\n\t\t\t\t\t', 'lat': '59.5449510501618', 'lng': '-139.7313094139099'}

        page_html = Selector(text=location["details"])
        location["address"] = str(page_html.xpath('//p[@class="address"]/strong/text()').get())
        text = str(page_html.xpath("text()").get())
        if "Phone: " in text:
            location["phone"] = text.split("Phone: ")[1]
        location["id"] = location["pid"]
