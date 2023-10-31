import json
import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.central_england_cooperative import set_operator
from locations.spiders.vapestore_gb import clean_address
from locations.user_agents import BROWSER_DEFAULT

OPERATORS = {
    "NCP": {"brand": "National Car Parks", "brand_wikidata": "Q6971273"},
    "APH": {"brand": "Airport Parking & Hotels", "brand_wikidata": None},
}


class NCPGB(SitemapSpider):
    name = "ncp_gb"
    sitemap_urls = ["https://www.ncp.co.uk/uploads/sitemap.xml"]
    sitemap_rules = [("/find-a-car-park/car-parks/", "parse_pois")]
    user_agent = BROWSER_DEFAULT
    download_delay = 2.0

    def parse_pois(self, response):
        if poi_match := re.search(r"'carparks'      : (\[.+}\]),", response.text):
            data = json.loads(poi_match.group(1))
            for poi in data:
                item = DictParser.parse(poi)
                item["street_address"] = clean_address([poi["addressLine1"], poi["addressLine2"], poi["addressLine3"]])
                item["website"] = response.urljoin(poi["clickUrl"])
                item["ref"] = poi.get("carParkHeadingID")
                item["name"] = poi.get("carParkTitle")

                supplier = poi["supplier"] or "NCP"
                if operator := OPERATORS.get(supplier):
                    set_operator(operator, item)
                else:
                    self.crawler.stats.inc_value("ncp/unknown_supplier/{}".format(supplier))

                apply_category(Categories.PARKING, item)

                apply_yes_no("surveillance", item, poi["cctv"] == "Y")
                apply_yes_no(Extras.TOILETS, item, poi["customerToilets"] == "Customer Toilets")
                apply_yes_no("supervised", item, poi["mannedSite"] == "Staffed Site")

                if spaces := poi["numberOfSpaces"]:
                    item["extras"]["capacity"] = str(spaces)

                if num_dis := poi.get("numberOfDisabledBays"):
                    if num_dis != "0":
                        item["extras"]["capacity:disabled"] = num_dis

                yield item
