from urllib.parse import urlparse

import scrapy
from scrapy.commands import BaseRunSpiderCommand
from scrapy.exceptions import UsageError
from scrapy.spiders.sitemap import iterloc
from scrapy.utils.sitemap import Sitemap, sitemap_urls_from_robots

from locations.user_agents import BROSWER_DEFAULT


class MySitemapSpider(scrapy.spiders.SitemapSpider):
    name = "my_sitemap_spider"
    user_agent = BROSWER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False}
    pages = False
    download_delay = 0.5

    def _parse_sitemap(self, response):
        if response.url.endswith("/robots.txt"):
            for url in sitemap_urls_from_robots(response.text, base_url=response.url):
                if not self.pages:
                    print(url)
                yield scrapy.Request(url, callback=self._parse_sitemap)
        else:
            body = self._get_sitemap_body(response)
            if body is None:
                print("invalid sitemap response: " + response.url)
                return

            s = Sitemap(body)
            it = self.sitemap_filter(s)

            if s.type == "sitemapindex":
                for loc in iterloc(it, self.sitemap_alternate_links):
                    if any(x.search(loc) for x in self._follow):
                        if not self.pages:
                            print(loc)
                        yield scrapy.Request(loc, callback=self._parse_sitemap)
            elif s.type == "urlset":
                for loc in iterloc(it, self.sitemap_alternate_links):
                    if self.pages:
                        print(loc)


class SitemapCommand(BaseRunSpiderCommand):
    requires_project = True
    default_settings = {"LOG_ENABLED": False}

    def syntax(self):
        return "[options] <root URL | robots.txt URL | sitemap URL>"

    def short_desc(self):
        return "Probe website robots.txt / sitemap.xml for spider development insights"

    def add_options(self, parser):
        super().add_options(parser)
        parser.add_argument(
            "--pages",
            action="store_true",
            help="print HTTP page links rather than sitemap XML links, helps identify POI pages",
        )
        parser.add_argument(
            "--stats",
            action="store_true",
            help="show crawler stats",
        )

    def run(self, args, opts):
        if len(args) != 1:
            raise UsageError("Please specify a URL for the SitemapSpider")

        url = args[0]
        parsed = urlparse(url)
        if parsed.path.replace("/", "") == "":
            # If URL has no path data then take a chance on robots.txt being there to help.
            url = parsed.scheme + "://" + parsed.netloc + "/robots.txt"
        MySitemapSpider.sitemap_urls = [url]

        MySitemapSpider.pages = opts.pages

        crawler = self.crawler_process.create_crawler(MySitemapSpider, **opts.spargs)
        self.crawler_process.crawl(crawler)
        self.crawler_process.start()
        if opts.stats:
            for k, v in crawler.stats.get_stats().items():
                print(k + ": " + str(v))
