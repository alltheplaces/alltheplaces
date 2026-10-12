from locations.spiders.albertsons import AlbertsonsSpider


class SafewaySpider(AlbertsonsSpider):
    name = "safeway"
    item_attributes = {"brand": "Safeway", "brand_wikidata": "Q1508234"}
    allowed_domains = ["safeway.com"]
    sitemap_urls = [
        "https://local.safeway.com/sitemap.xml",
        "https://local.pharmacy.safeway.com/sitemap.xml",
        "https://local.fuel.safeway.com/sitemap.xml",
    ]
    sitemap_rules = [
        (r"^https://local\.(?:fuel\.|pharmacy\.)?safeway\.com/safeway/\w\w/[-\w]+/[-\w]+\.html$", "parse_sd"),
    ]
