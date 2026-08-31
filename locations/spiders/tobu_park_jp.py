from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature

# A single facility page can list more than one type (e.g. a bicycle park
# that also has a motorcycle section), so one item is yielded per type
# found rather than picking a single amenity for the whole page.
CATEGORY_MAP = {
    "car-parking": Categories.PARKING,
    "bicycle-parking": Categories.BICYCLE_PARKING,
    "bike-parking": Categories.MOTORCYCLE_PARKING,
    "bicycle-rental": Categories.BICYCLE_RENTAL,
}


class TobuParkJPSpider(SitemapSpider):
    name = "tobu_park_jp"
    item_attributes = {"brand": "TOBU PARK", "brand_wikidata": "Q131275047"}
    sitemap_urls = ["https://www.tobu-re-parking.jp/parking-sitemap.xml"]

    def parse(self, response):
        name = response.css("h1.title-h1__jp::text").get()
        center = response.css("gmp-map::attr(center)").get()
        if not name or not center:
            return
        lat, _, lon = center.partition(",")

        address = " ".join(
            t.strip() for t in response.xpath('//tr[th[normalize-space()="所在地"]]/td//text()').getall() if t.strip()
        )

        post_id = response.url.rstrip("/").rsplit("/", 1)[-1].removesuffix(".html")

        for li in response.css("ul.tag-type li"):
            slug = li.attrib.get("class", "").removeprefix("tag-type__")
            category = CATEGORY_MAP.get(slug)
            if not category:
                continue

            item = Feature()
            item["ref"] = f"{post_id}_{slug}"
            item["name"] = name.strip()
            item["lat"] = lat
            item["lon"] = lon
            item["addr_full"] = address
            item["country"] = "JP"
            item["website"] = response.url

            apply_category(category, item)

            yield item
