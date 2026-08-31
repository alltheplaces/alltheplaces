import argparse
import sys

from scrapy.commands import ScrapyCommand
from scrapy.exceptions import UsageError

from locations.extensions.add_lineage import VALID_GROUPS, lineage_for_group, spider_class_to_lineage


class ListGroupCommand(ScrapyCommand):
    requires_project = True
    default_settings = {"LOG_ENABLED": False}

    def syntax(self) -> str:
        return "<group>"

    def short_desc(self) -> str:
        return "List spiders belonging to a run group"

    def long_desc(self) -> str:
        groups = ", ".join(sorted(VALID_GROUPS))
        return f"List spider names belonging to the given run group. Valid groups: {groups}"

    def run(self, args: list[str], opts: argparse.Namespace) -> None:
        if len(args) != 1:
            raise UsageError()

        group = args[0]
        try:
            lineage_for_group(group)
        except ValueError as e:
            sys.stderr.write(str(e) + "\n")
            self.exitcode = 1
            return

        if not self.crawler_process:
            raise RuntimeError("Crawler process not defined")

        for spider_name in sorted(self.crawler_process.spider_loader.list()):
            spidercls = self.crawler_process.spider_loader.load(spider_name)
            spider_lineage = spider_class_to_lineage(spidercls)
            if spider_lineage.group == group:
                sys.stdout.write(f"{spider_name}\n")
