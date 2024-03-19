from scrapy import signals
from scrapy.commands import BaseRunSpiderCommand
from scrapy.crawler import CrawlerProcess
from scrapy.exceptions import UsageError
from scrapy.utils.project import get_project_settings

from locations.storefinder_detector import StorefinderDetectorSpider


# Detect presence of a store finder at a given URL, and return a pre-filled Spider.
class SfCommand(BaseRunSpiderCommand):
    requires_project = True
    default_settings = {"LOG_LEVEL": "ERROR"}

    def syntax(self):
        return "[options] <URL to scan for store finder>"

    def short_desc(self):
        return "Detect presence of a store finder at a given URL, and return a pre-filled Spider"

    def add_options(self, parser):
        super().add_options(parser)
        parser.add_argument(
            "--brand-wikidata",
            dest="brand_wikidata",
            help="attempt to pre-fill brand name and NSI category based on supplied Wikidata Q-code",
        )
        parser.add_argument(
            "--operator-wikidata",
            dest="operator_wikidata",
            help="attempt to pre-fill operator name and NSI category based on supplied Wikidata Q-code",
        )
        parser.add_argument(
            "--spider-key",
            dest="spider_key",
            help="pre-fill a spider key (should match the desired file name for the spider with optionally one or more _xx suffixes where xx is an ISO 3166-2 code)",
        )
        parser.add_argument(
            "--spider-class-name",
            dest="spider_class_name",
            help="pre-fill a spider class name (should be in title case and suffixed with 'Spider')",
        )

    def run(self, args, opts):
        if len(args) != 1:
            raise UsageError("Please specify single URL that is desired to be scanned for a store finder.")

        if not args[0].startswith("http"):
            raise UsageError(
                "A http or https URL scheme is required when specifying the single URL that is desired to be scanned for a store finder."
            )

        settings = get_project_settings()
        settings.set("ITEM_PIPELINES", {})
        settings.set("FEED_EXPORTERS", {})
        settings.set("LOG_LEVEL", "ERROR")
        process = CrawlerProcess(settings)
        crawler = process.create_crawler(StorefinderDetectorSpider)
        crawler.signals.connect(self.print_spider_code, signal=signals.item_scraped)
        process.crawl(
            crawler,
            url=args[0],
            brand_wikidata=opts.brand_wikidata,
            operator_wikidata=opts.operator_wikidata,
            spider_key=opts.spider_key,
            spider_class_name=opts.spider_class_name,
        )
        process.start()

    def print_spider_code(self, item):
        for base_class in item["spider"].__bases__:
            if not callable(getattr(base_class, "generate_spider_code")):
                continue
            print(base_class.generate_spider_code(item["spider"]))
            break
