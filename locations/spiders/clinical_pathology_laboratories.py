import scrapy

from locations.items import Feature


class ClinicalPathologyLaboratoriesSpider(scrapy.Spider):
    name = "clinical_pathology_laboratories"
    item_attributes = {
        "brand": "Clinical Pathology Laboratories",
        "brand_wikidata": "Q91911320",
    }
    allowed_domains = ["cpllabs.com"]
    start_urls = [
        "https://www.zeemaps.com/emarkers?g=3025292&k=REGULAR&e=true&_dc=0.9710587730049409",
    ]

    def parse(self, response):
        for item in response.json():
            properties = {
                "name": item["nm"],
                "street_address": item["s"],
                "city": item["city"],
                "state": item["state"],
                "postcode": item["zip"],
                "country": "US",
                "ref": item["id"],
                "lat": item["lat"],
                "lon": item["lng"],
            }
            yield Feature(**properties)
