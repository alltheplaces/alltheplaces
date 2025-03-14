from scrapy.spiders import CSVFeedSpider

from locations.items import Feature


class CatScaleCAUSSpider(CSVFeedSpider):
    name = "cat_scale_ca_us"
    allowed_domains = ["catscale.com"]
    start_urls = ["https://catscale.com/exl.php"]

    item_attributes = {
        "brand": "CAT Scale",
        "brand_wikidata": "Q111631907",
    }

    def parse_row(self, response, row):
        item = Feature()
        item["ref"] = row["CATScaleNumber"]
        item["state"] = row["State"]
        item["city"] = row["InterstateCity"]
        item["located_in"] = row["TruckstopName"]
        item["street_address"] = row["InterstateAddress"]
        item["postcode"] = row["InterstatePostalCode"]
        item["country"] = "US" if row["InterstatePostalCode"].isdigit() else "CA"
        item["phone"] = row["PhoneNumber"]
        item["extras"]["fax"] = row["FaxNumber"]
        item["lat"] = row["Latitude"]
        item["lon"] = row["Longitude"]
        item["extras"]["located_in:website"] = row["URL"]
        return item
