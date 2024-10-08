import scrapy

from locations.dict_parser import DictParser


class TheBodyShopSpider(scrapy.spiders.SitemapSpider):
    name = "the_body_shop"
    item_attributes = {"brand": "The Body Shop", "brand_wikidata": "Q837851"}
    allowed_domains = ["thebodyshop.com"]
    sitemap_urls = ["https://www.thebodyshop.com/sitemap.xml"]

    parse_pages = {
        "/en-gb/": "uk",
        "/es-es/": "es",
        "/en-au/": "au",
        "/en-ca/": "ca",
        "/en-us/": "us",
        "/de-de/": "de",
        "/en-sg/": "sg",
        "/da-dk/": "dk",
        "/sv-se/": "se",
        "/nl-nl/": "nl",
        "/fr-fr/": "fr",
        "/pt-pt/": "pt",
        "/de-at/": "at",
    }

    def _parse_sitemap(self, response):
        for x in super()._parse_sitemap(response):
            if ".xml" in x.url:
                yield x
            elif "/store-details" in x.url:
                store_id = x.url.split("/")[-1]
                for key in self.parse_pages:
                    if key in x.url:
                        yield scrapy.Request(
                            "https://api.thebodyshop.com/rest/v2/thebodyshop-{}/stores/{}".format(
                                self.parse_pages[key], store_id
                            ),
                            headers={"Accept": "application/json"},
                            cb_kwargs=dict(html_url=x.url),
                        )
                        break

    def parse(self, response, html_url):
        store = response.json()
        item = DictParser.parse(store)
        item["ref"] = store["address"]["id"]
        item["name"] = store["displayName"]
        item["website"] = html_url
        if isinstance(item["state"], dict):  # inconsistently string or dict
            item["state"] = item["state"]["name"]
        item["country"] = store["address"]["country"]["isocode"]
        return item
