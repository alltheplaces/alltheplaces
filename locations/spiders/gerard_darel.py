from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Clothes, apply_category, apply_clothes
from locations.structured_data_spider import StructuredDataSpider


class GerardDarelSpider(SitemapSpider, StructuredDataSpider):
    name = "gerard_darel"
    item_attributes = {
        "brand": "Gérard Darel",
        "brand_wikidata": "Q3123882",
    }
    sitemap_urls = ["https://boutiques.gerarddarel.com/en/sitemap.xml"]
    sitemap_rules = [
        (r"/gerard-darel", "parse_sd"),
    ]
    wanted_types = ["LocalBusiness"]
    drop_attributes = ["facebook"]

    def _parse_sitemap(self, response):
        """
        The Sitemap of this website is buggy, we need to add "/en" between the domain and the page.
        """
        for request in super()._parse_sitemap(response):
            # Modify the URL before the request is sent
            url_fragment = request.url.split("gerarddarel.com")
            yield request.replace(url=url_fragment[0] + "gerarddarel.com/en" + url_fragment[1])

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_CLOTHES, item)
        apply_clothes(Clothes.WOMEN, item)

        item["branch"] = (item.pop("name") or "").removeprefix("Gerard Darel ")

        yield item
