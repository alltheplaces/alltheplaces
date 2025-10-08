from scrapy import Request, Selector, Spider

from locations.dict_parser import DictParser

# Concentra is using a Sitecode SXA Search Service as documented at
# https://doc.sitecore.com/xp/en/developers/sxa/103/sitecore-experience-accelerator/the-sxa-search-service.html
#
# A maximum of 250 locations are returned per page of results.


class ConcentraUSSpider(Spider):
    name = "concentra_us"
    item_attributes = {"operator": "Concentra", "operator_wikidata": "Q5158304"}
    allowed_domains = ["concentra.com"]
    start_urls = [
        "https://www.concentra.com/sxa/search/results/?s={449ED3CA-26F3-4E6A-BF21-9808B60D936F}&itemid={739CBD3C-A3B6-4CA2-8004-BF6005BB28E9}&v={D907A7FD-050F-4644-92DC-267C1FDE200C}&g=&p=250&e="
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=f"{url}0", meta={"url": url, "offset": 0})

    def parse(self, response):
        for location in response.json()["Results"]:
            item = DictParser.parse(location)
            item["lat"] = location["Geospatial"]["Latitude"]
            item["lon"] = location["Geospatial"]["Longitude"]
            html = Selector(text=location["Html"])
            item["name"] = html.xpath('//div[@class="field-centername"]/text()').get().strip()
            item["street_address"] = html.xpath('//div[@class="field-addressline1"]/text()').get().strip()
            item["city"] = html.xpath('//span[@class="field-city"]/text()').get().strip()
            item["state"] = html.xpath('//span[@class="field-stateabbreviation"]/text()').get().strip()
            item["postcode"] = html.xpath('//span[@class="field-zipcode"]/text()').get().strip()
            item["phone"] = " ".join(html.xpath('//span[@class="field-mainphone"]/text()').getall()).strip()
            item["website"] = "https://www.concentra.com" + location["Url"]
            yield item

            if response.meta["offset"] < response.json()["Count"]:
                new_offset = response.meta["offset"] + 250
                new_url = response.meta["url"] + str(new_offset)
                yield Request(url=new_url, meta={"url": response.meta["url"], "offset": new_offset})
