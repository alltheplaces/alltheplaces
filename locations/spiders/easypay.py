from scrapy.spiders import CSVFeedSpider

from locations.dict_parser import DictParser


class EasypaySpider(CSVFeedSpider):
    name = "easypay"  # the name is not set to easypay_bg, because then name would be used to extract "country" by the pipeline, and "country" in every item would be set to "BG", which is wrong.
    item_attributes = {"brand": "EasyPay", "brand_wikidata": "Q110583289"}
    start_urls = ["https://www.easypay.bg/site/en/offices.csv"]
    delimiter = "|"
    headers = ["id", "lat", "lon", "post_code", "address", "phone", "opening_hours", "operator", "type"]

    def parse_row(self, response, row):
        item = DictParser.parse(row)
        item["extras"]["operator"] = row["operator"]
        yield item
