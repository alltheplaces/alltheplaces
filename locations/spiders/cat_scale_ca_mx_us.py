from scrapy.spiders import CSVFeedSpider

from locations.dict_parser import DictParser
from locations.categories import apply_category

class CatScaleCAMXUSSpider(CSVFeedSpider):
    name = "cat_scale_ca_mx_us"
    allowed_domains = ["catscale.com"]
    start_urls = ["https://catscale.com/exl.php"]

    item_attributes = {
        "brand": "CAT Scale",
        "brand_wikidata": "Q111631907",
    }

    def parse_row(self, response, row):
        item = DictParser.parse(row)
        item["ref"] = row["CATScaleNumber"]
        item["city"] = row["InterstateCity"]
        item["located_in"] = row["TruckstopName"]
        item["street_address"] = row["InterstateAddress"]
        item["postcode"] = row["InterstatePostalCode"]
        item.pop("website")
        item["extras"]["fax"] = row["FaxNumber"]
        item["extras"]["located_in:website"] = row["URL"]
        apply_category({"amenity": "weighbridge"}, item)
        return item
