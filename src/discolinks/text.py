import attrs
from rich import print
from rich.markup import escape
from rich.tree import Tree

from . import analyzer, outcome


@attrs.frozen
class Converter(outcome.Converter[str]):
    def convert_page(self, page: outcome.Page) -> str:
        return f"[red]{escape(str(page.code))}[/red]"

    def convert_redirect(self, redirect: outcome.Redirect) -> str:
        return escape(str(redirect.code))

    def convert_request_error(self, error: outcome.RequestError) -> str:
        return f"[red]{escape(str(error.msg))}[/red]"

    def convert_unknown(self, unknown: outcome.Unknown) -> str:
        assert False, "`Unknown` result isn't supposed to be shown"


def print_results(analysis: analyzer.Analysis) -> None:
    failed_style = "bold dim" if analysis.ok() else "bold red"
    root_label = (
        f"📂 Results: [bold]{analysis.stats.total}[/bold] links"
        f" ([bold green]{analysis.stats.ok}[/bold green] ok,"
        f" [{failed_style}]{analysis.stats.failed}[/{failed_style}] failed)"
    )
    tree = Tree(root_label, guide_style="dim")

    for (url, info) in analysis.pages.items():
        bad_links = [link for link in info.links if not link.ok()]

        if not bad_links:
            continue

        branch = tree.add(f"📄 {escape(str(url))}", style="bold")

        for link in bad_links:
            items = link.results.convert_with(Converter())
            results = " → ".join(items)
            branch.add(f"🔗 [blue]{escape(link.href)}[/blue]: {results}")

    print(tree)
