import requests
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class EdwardJonesSpider(SitemapSpider, StructuredDataSpider):
    name = "edwardjones"
    item_attributes = {"brand": "Edward Jones", "brand_wikidata": "Q5343830"}
    allowed_domains = ["www.edwardjones.com"]
    sitemap_urls = ["https://www.edwardjones.com/us-en/sitemap/financial-advisor/sitemap.xml"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        oh = OpeningHours()
        oh.from_linked_data(ld_data, time_format="%H:%M:%S")
        item["opening_hours"] = oh.as_opening_hours()

        flag = True
        page = 1
        while flag:
            url = "https://www.edwardjones.com/api/v3/financial-advisor/results?q={postcode}&distance=75&distance_unit=mi&page={page}&searchtype=2".format(
                postcode=item["postcode"], page=page
            )

            headers = {
                "Host": "www.edwardjones.com",
                "Accept": "application/json",
                "Referer": "https://www.edwardjones.com/us-en/search/financial-advisor/results",
            }
            response = requests.get(url, headers=headers, data={}).json()

            for x in response["results"]:
                if item["website"].endswith(x["faUrl"]):
                    item["lat"] = x["lat"]
                    item["lon"] = x["lon"]
                    flag = False

            count = len(response["results"])
            if count < response["itemsPerPage"] or count == 0:
                flag = False
            else:
                page = page + 1

        yield item
