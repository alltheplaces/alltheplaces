import scrapy

from locations.dict_parser import DictParser


class RedLionSpider(scrapy.spiders.SitemapSpider):
    name = "redlion"
    sitemap_urls = ["https://www.redlion.com/sitemap.xml"]
    my_brands = {
        "/americas-best-value-inn/": ("Americas Best Value Inn", "Q4742512"),
        "/canadas-best-value-inn/": ("Canadas Best Value Inn", "Q4742512"),
        "/guesthouse-extended-stay/": ("Guesthouse Extended Stay", "Q4742512"),
        "/knights-inn/": ("Knights Inn", "Q6422409"),
        "/red-lion-hotels/": ("Red Lion Hotels", "Q25047720"),
        "/red-lion-inn-suites/": ("Red Lion Hotels", "Q25047720"),
    }

    def _parse_sitemap(self, response):
        for x in super()._parse_sitemap(response):
            for k, v in self.my_brands.items():
                if k in x.url:
                    url = x.url + "/page-data.json"
                    url = url.replace("redlion.com/", "redlion.com/page-data/")
                    yield scrapy.Request(url, cb_kwargs=dict(website=x.url, brand=v))

    def parse(self, response, website, brand):
        hotel = response.json()["result"]["data"]["hotel"]
        item = DictParser.parse(hotel["address"])
        item["website"] = item["ref"] = website
        item["phone"] = hotel.get("phone")
        item["state"] = hotel["address"].get("administrative_area")
        item.update(hotel["lat_lon"])
        item["brand"], item["brand_wikidata"] = brand
        item["image"] = hotel["banner_images"][0]["url"]
        yield item
