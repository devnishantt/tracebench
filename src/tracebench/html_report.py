from jinja2 import Environment, PackageLoader, select_autoescape
from .artifacts import Report
from .presentation import presentation

def render_html(report: Report) -> str:
    environment = Environment(loader=PackageLoader('tracebench', 'templates'), autoescape=select_autoescape(['html'], default=True))
    return environment.get_template('report.html').render(report=report, view=presentation(report))
