from html import unescape

from chompjs import parse_js_object
from scrapy import Spider

from locations.categories import Categories
from locations.items import Feature


class JamesRetailGBSpider(Spider):
    name = "james_retail_gb"
    allowed_domains = ["www.google.com"]
    start_urls = ["https://www.google.com/maps/d/embed?mid=10xMk9hAqaEABqBznMGPdK54TcTDlbTk"]
    brands = {
        "GTNEWS": {"brand": "GT News", "brand_wikidata": "Q124473779", "extras": Categories.SHOP_NEWSAGENT.value},
        "SUPERNEWS": {"brand": "Supernews", "brand_wikidata": "Q124473643", "extras": Categories.SHOP_NEWSAGENT.value},
    }

    def parse(self, response):
        js_blob = response.xpath('//script[contains(text(), "var _pageData = ")]/text()').get()
        js_blob = js_blob.split('var _pageData = "', 1)[1].split('";', 1)[0]
        json_data = parse_js_object(js_blob)
        for location in json_data[1][6][0][4]:
            properties = {
                "ref": unescape(location[-2][-1]).replace('\\"', "").replace("\xa0", " ").strip(),
                "name": unescape(location[-1][0][0]).replace('\\"', "").replace("\xa0", " ").strip(),
                "lat": location[-2][4][0],
                "lon": location[-2][4][1],
            }
            if "SUPERNEWS" in properties["name"].upper():
                properties.update(self.brands["SUPERNEWS"])
            elif "GT NEWS" in properties["name"].upper():
                properties.update(self.brands["GTNEWS"])
            elif "SELECT CONVENIENCE" in properties["name"].upper():
                # Should be included in bargain_booze_gb spider as
                # James Retail is an operator of this franchise.
                continue
            else:
                # Head office, other unknown locations seemingly not
                # branded in a consistent way.
                continue
            yield Feature(**properties)
