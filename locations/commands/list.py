import argparse

from scrapy.commands.list import Command
from scrapy.spiderloader import get_spider_loader

from locations.exporters.geojson import find_spider_class


class ListCommand(Command):

    def run(self, args: list[str], opts: argparse.Namespace) -> None:
        assert self.settings is not None
        spider_loader = get_spider_loader(self.settings)
        if opts.skip_addresses is True:
            for spider_name in spider_loader.list():
                spider_cls = find_spider_class(spider_name)
                if not spider_cls.__module__.startswith("locations.spiders.addresses."):
                    print(spider_name)
        else:
            print("\n".join(sorted(spider_loader.list())))
            return

    def add_options(self, parser: argparse.ArgumentParser) -> None:
        super().add_options(parser)
        parser.add_argument(
            "--skip-addresses",
            action="store_true",
            dest="skip_addresses",
            help="Ignore address spiders",
        )
