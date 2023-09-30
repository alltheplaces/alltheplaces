from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Clothes, apply_category, apply_clothes
from locations.structured_data_spider import StructuredDataSpider


class GapUSSpider(SitemapSpider, StructuredDataSpider):
    name = "gap_us"
    item_attributes = {"brand": "Gap", "brand_wikidata": "Q420822"}
    allowed_domains = ["www.gap.com"]
    sitemap_urls = ["https://www.gap.com/stores/sitemap.xml"]
    sitemap_rules = [(r"https://www\.gap\.com/stores/\w\w/\w+/gap-(\d+)\.html$", "parse_sd")]
    requires_proxy = True

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = response.xpath('normalize-space(//div[@class="location-name"]/text())').get()

        types = response.xpath('normalize-space(//div[@class="store-carries"]/text())').get()

        if types == "Gap Factory Store":
            item["brand"] = "Gap Factory Store"
        else:
            item["brand"] = "Gap"
            clothes = []
            if "GapBody" in types:
                clothes.append(Clothes.UNDERWEAR.value)
            if "GapMaternity" in types:
                clothes.append(Clothes.MATERNITY.value)
            if "babyGap" in types:
                clothes.append(Clothes.BABY.value)
            if "GapKids" in types:
                clothes.append(Clothes.CHILDREN.value)
            apply_clothes(clothes, item)

        item["image"] = None

        apply_category(Categories.SHOP_CLOTHES, item)

        yield item
