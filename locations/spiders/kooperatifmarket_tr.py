import scrapy

from locations.items import Feature


class KooperatifmarketTrSpider(scrapy.Spider):
    name = "kooperatifmarket_tr"
    item_attributes = {"brand_wikidata": "Q127328776"}
    start_urls = ["https://www.kooperatifmarket.com.tr/api/stores"]

    def parse(self, response):
        for poi in response.json():
            item = Feature()
            item["ref"] = item["branch"] = poi["marketAdi"]
            item["state"] = poi["marketIl"]
            item["extras"]["addr:district"] = poi["marketIlce"]
            item["lat"] = float(poi["marketEnlem"])
            item["lon"] = float(poi["marketBoylam"])
            item["addr_full"] = poi["marketAdres"]
            yield item
