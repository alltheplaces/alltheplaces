import argparse
import os
import sys

from scrapy.commands import ScrapyCommand
from scrapy.exceptions import UsageError


class FilenameCommand(ScrapyCommand):
    requires_project = True
    default_settings = {"LOG_ENABLED": False}

    def syntax(self) -> str:
        return "<spider>"

    def short_desc(self) -> str:
        return "Get spider filename"

    def long_desc(self) -> str:
        return "Get the filename for the given spider name"

    def _err(self, msg: str) -> None:
        sys.stderr.write(msg + os.linesep)
        self.exitcode = 1

    def run(self, args: list[str], opts: argparse.Namespace) -> None:
        if len(args) != 1:
            raise UsageError()

        if not self.crawler_process:
            raise RuntimeError("Crawler process not defined")

        try:
            spidercls = self.crawler_process.spider_loader.load(args[0])
        except KeyError:
            return self._err(f"Spider not found: {args[0]}")

        sfile = sys.modules[spidercls.__module__].__file__
        if not sfile:
            return self._err(f"Spider not found: {args[0]}")
        sfile = sfile.replace(".pyc", ".py")
        sfile = os.path.relpath(sfile)

        sys.stdout.write(f"{sfile}\n")
