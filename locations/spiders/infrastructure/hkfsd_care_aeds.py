from html import unescape

from scrapy.spiders import CSVFeedSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class HKFSDCareAEDsSpider(CSVFeedSpider):
    # writing this is painful. most of the time, the name given is completely useless
    # i.e. every AED owned by the airport is just called 'Airport Authority Hong Kong'
    # there are a few decent enums, but the service hours exist as a 'remarks' field that has no concise format
    # basically however the maintainer adds it to the database
    # it could be anything from actual hours to 'i dunno, does our website say we're open?'
    # but it *is* first party though, so there's that
    name = "hkfsd_care_aeds"
    allowed_domains = ["es.hkfsd.gov.hk"]
    start_urls = ["https://es.hkfsd.gov.hk/aed_api/export_aed.php?lang=EN"]
    delimiter = ","
    quotechar = '"'
    no_refs = True

    item_attributes = {
        # Uncomment and populate if known
        # "brand": "None",
        # "brand_wikidata": "None",
        # "operator": "None",
        # "operator_wikidata": "None",
    }

    # Do any adaptations you need here
    # def adapt_response(self, response):
    # fix for some values which have been single or even double encoded into HTML entities
    # fixed_response = response.replace(body=unescape(unescape(response.text)))
    # return fixed_response

    def parse_row(self, response, row):
        i = Feature()
        i["located_in"] = unescape(row["AED Name"])
        i["lat"] = row["Location Google Map coordinate: latitude"]
        i["lon"] = row["Location Google Map coordinate: longitude"]
        i["addr_full"] = row["AED Address"]
        i["extras"] = {
            "defibrillator:location": row["Detailed location of the AED installed"],
            "description": row["AED remark"],
            "manufacturer": row["AED brand"],
            "model": row["AED model"],
        }
        apply_category(Categories.DEFIBRILLATOR, i)
        return i
