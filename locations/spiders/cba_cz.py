import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class CbaCZSpider(SitemapSpider):
    name = "cba_cz"
    item_attributes = {"brand": "CBA", "brand_wikidata": "Q779845"}
    sitemap_urls = ["https://www.cba.cz/wp-sitemap.xml"]
    sitemap_follow = ["posts-page"]
    sitemap_rules = [(r"/prodejny-cba/.+", "parse")]
    no_refs = True

    def parse(self, response, **kwargs):
        for shop in response.xpath('//*[contains(text(),"Název")]/ancestor::div[@class="row_fix_width"]'):
            item = Feature()
            if name := re.search(r"Název:\s*(?:<br>)?(.+?)<br>", shop.get()):
                item["branch"] = name.group(1).replace("\xa0", "")
            item["addr_full"] = merge_address_lines(shop.xpath("./div[3]//p/text()").getall())
            if map_url := shop.xpath('//iframe[contains(@src, "maps")]/@src').get():
                item["lat"], item["lon"] = url_to_coords(map_url)
            item["website"] = response.url
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
