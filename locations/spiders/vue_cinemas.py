import json

from scrapy.spiders import SitemapSpider

from locations.items import Feature


class VueCinemasSpider(SitemapSpider):
    name = "vue_cinemas"
    item_attributes = {"brand": "Vue", "brand_wikidata": "Q2535134"}
    sitemap_urls = ["https://www.myvue.com/sitemap.xml"]
    sitemap_rules = [(r"/whats-on$", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        jsondata = response.xpath("//script[@id='__NEXT_DATA__']/text()").get()
        cinemadata = json.loads(jsondata)["props"]["pageProps"]["layoutData"]["sitecore"]["context"]["cinema"]

        item["lat"], item["lon"] = cinemadata["cinemaLocationCoordinates"]["value"].split(",")
        item["website"] = response.url.replace("/whats-on", "")
        item["ref"] = item["website"].replace("https://www.myvue.com/cinema/", "")
        item["name"] = "Vue Cinema"
        item["branch"] = item["ref"].replace("-", " ").title()
        item["addr_full"] = cinemadata["cinemaAddress"]["value"].replace("\n", ",")
        yield item
