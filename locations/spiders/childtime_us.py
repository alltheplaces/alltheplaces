import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class ChildtimeUSSpider(SitemapSpider, StructuredDataSpider):
    """Each school publishes itself as linked data, and the site keeps a sitemap of
    nothing but schools, so that is what is crawled.

    The find-a-school pages are not used: they are built by script, and they mix in
    the other Learning Care Group brands, which have to be told apart by a brand
    attribute on each card. The schools in this sitemap are all Childtime's own, and
    the spider checks that before publishing one.
    """

    name = "childtime_us"
    item_attributes = {"brand": "Childtime", "brand_wikidata": "Q64877793"}
    sitemap_urls = ["https://www.childtime.com/sitemaps/www-childtime-com-schools.xml/"]
    sitemap_rules = [(r"/your-local-school/[^/]+/$", "parse_sd")]
    # Each school is typed as all of Preschool, ChildCare and LocalBusiness at once,
    # so asking for more than one of them would parse every school several times over.
    wanted_types = ["Preschool"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        # The schools are named "Childtime of <town>", or after their own road where a
        # town has more than one of them.
        name = item.pop("name", None) or ""
        if not name.lower().startswith("childtime"):
            self.logger.warning(f"Skipping {response.url}, which is named {name!r}")
            return
        item["branch"] = re.sub(r"^Childtime\s+(?:of|on|at)?\s*", "", name).strip() or None

        # Each school states the id it is known by, which is also the tail of its slug.
        item["ref"] = ld_data.get("branchCode") or response.url.rstrip("/").rsplit("-", 1)[-1]
        item["website"] = response.url

        # The page also carries the director's name and photograph and a list of
        # parents' reviews. None of that belongs in a POI, so it is left behind.
        item.pop("image", None)

        apply_category(Categories.KINDERGARTEN, item)
        item["extras"]["preschool"] = "yes"
        yield item
