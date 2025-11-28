import json

from scrapy import Request
from scrapy.spiders import CSVFeedSpider

from locations.categories import Categories, apply_category, apply_yes_no
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.arnold_clark import ArnoldClarkSpider
from locations.spiders.kwik_fit_gb import KwikFitGBSpider


class GovMotGBSpider(CSVFeedSpider):
    name = "gov_mot_gb"
    dataset_attributes = {
        "license": "Open Government Licence v3.0",
        "license:website": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
        "license:wikidata": "Q99891702",
        "attribution": "required",
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0.",
    }  # https://www.whatdotheyknow.com/request/re_use_of_active_mot_test_statio

    def start_requests(self):
        yield Request(
            url="https://www.gov.uk/government/publications/active-mot-test-stations", callback=self.get_dataset
        )

    def get_dataset(self, response, **kwargs):
        ld = json.loads(
            response.xpath('//script[@type="application/ld+json"][contains(text(), "Dataset")]/text()').get()
        )
        for dist in ld["distribution"]:
            if dist["encodingFormat"] == "text/csv" and dist["name"] == "Active MOT test stations":
                yield Request(url=dist["contentUrl"])

    def parse_row(self, response, row):
        item = Feature()
        item["ref"] = row["Site_Number"]
        item["name"] = row["Trading_Name"]
        item["street_address"] = merge_address_lines([row["Address1"], row["Address2"], row["Address3"]])
        item["city"] = row["Town"]
        item["postcode"] = row["Postcode"]
        item["phone"] = row["Phone"]
        # Class 1	Class 2	Class 3	Class 4	Class 5	Class 7

        if item["name"] == "KWIK FIT":
            item.update(KwikFitGBSpider.item_attributes)
        elif item["name"] == "HALFORDS AUTOCENTRE":
            item.update({"brand": "Halfords Autocentre", "brand_wikidata": "Q5641894"})
        elif item["name"] == "ATS EUROMASTER LIMITED":
            item.update({"brand": "ATS Euromaster", "brand_wikidata": "Q4654920"})
        elif item["name"] == "ARNOLD CLARK":
            item.update(ArnoldClarkSpider.item_attributes)
        elif item["name"] == "FORMULA ONE AUTOCENTRES LIMITED":
            item.update({"brand": "Formula One Autocentres", "brand_wikidata": "Q79239635"})
        elif item["name"] in ["N/A", "VARIOUS"]:
            item["name"] = None

        apply_category(Categories.SHOP_CAR_REPAIR, item)
        apply_yes_no("service:vehicle:mot", item, True)

        yield item
