from dataclasses import dataclass


@dataclass(frozen=True)
class DashboardModuleDefinition:
    id: str
    label: str
    area: str
    default_enabled: bool
    render_handler: str


DASHBOARD_MODULE_DEFINITIONS = (
    DashboardModuleDefinition(
        id="today_summary",
        label="Today Summary",
        area="right",
        default_enabled=True,
        render_handler="render_today_summary",
    ),
    DashboardModuleDefinition(
        id="now_next",
        label="Now / Next",
        area="primary",
        default_enabled=True,
        render_handler="render_live_carousel_slide",
    ),
    DashboardModuleDefinition(
        id="headlines",
        label="Top Headlines",
        area="primary",
        default_enabled=True,
        render_handler="render_headline_cards",
    ),
    DashboardModuleDefinition(
        id="right_calendar",
        label="Right Calendar",
        area="right",
        default_enabled=True,
        render_handler="render_next_four_weeks_calendar",
    ),
)

DASHBOARD_MODULES = {
    module.id: module.label
    for module in DASHBOARD_MODULE_DEFINITIONS
}

DEFAULT_DASHBOARD_MODULES = {
    module.id
    for module in DASHBOARD_MODULE_DEFINITIONS
    if module.default_enabled
}
