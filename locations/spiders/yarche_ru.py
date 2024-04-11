import scrapy

from locations.items import Feature


class YarcheRUSpider(scrapy.Spider):
    name = "yarche_ru"
    allowed_domains = ["xn--e1avv4a.xn--p1ai"]
    item_attributes = {"brand": "Ярче!", "brand_wikidata": "Q102254456"}
    start_urls = ["https://xn--e1avv4a.xn--p1ai/"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    def parse(self, response):
        for region_id in response.xpath('//select[@id="current_region"]/option/@value').getall():
            yield scrapy.Request(f"https://xn--e1avv4a.xn--p1ai/shops/?region={region_id}", callback=self.parse_pois)

    def parse_pois(self, response):
        for poi in response.xpath('//a[@class="shop_address"]'):
            item = Feature()
            item["ref"] = poi.xpath("./@data-id").get()
            item["street_address"] = poi.xpath("./text()").get(default="").strip()
            if coords := poi.xpath("./@data-coords").get():
                try:
                    item["lat"], item["lon"] = [c.strip() for c in coords.split(",")]
                except ValueError as e:
                    self.logger.error(f"Failed to parse coords {coords}: {e}")
            yield item
