from scrapy import Spider

from locations.items import Feature


class AswakAssalamMASpider(Spider):
    name = "aswak_assalam_ma"
    item_attributes = {"brand": "Aswak Assalam", "brand_wikidata": "Q2868678"}
    allowed_domains = ["www.aswakassalam.com"]
    start_urls = ["https://www.aswakassalam.com/nos-magasins/"]

    def parse(self, response):
        for location in response.xpath("//select[@id='select-opt-aswak-map']/option"):
            # Example: data-content="&lt;strong&gt;Casablanca&lt;/strong&gt;&lt;br /&gt;1, château Ykem, route Ouled Ziane Tel : 0522 28 34 00"
            html = location.xpath("@data-content").get().split("<br />")[1]

            item = Feature()
            item["ref"] = location.xpath("text()").get().strip()
            item["lat"] = location.xpath("@data-lat").get()
            item["lon"] = location.xpath("@data-lon").get()
            item["name"] = location.xpath("text()").get().strip()
            item["city"] = location.xpath("text()").get().strip()
            if "Tel : " in html:
                item["phone"] = html.split("Tel : ")[1]
            item["street_address"] = html.split("\n")[0]

            yield item
