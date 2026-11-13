"""What a role may see (dashboard pages) and what it may do (service areas).

The page list is a convenience for the sidebar; the area check is the control
the service enforces on every request.
"""

from config import config


def resolve_pages_for_role(role_name):
    """The role's pages in sidebar order, as a fresh list; [] for an unknown role."""
    return list(config.ROLE_PAGE_ACCESS.get(role_name, []))


def check_role_may_open_area(role_name, area_name):
    """True only when config.ROLE_AREA_ACCESS lists this area for this role."""
    return area_name in config.ROLE_AREA_ACCESS.get(role_name, [])


def resolve_area_for_path(request_path, request_method):
    """The one area a request belongs to, or '' for a path no entry covers."""
    # Submitting a decision is the review area wherever it sits (Safety Rule 02).
    if request_method.upper() == "POST" and request_path.endswith(config.REVIEW_PATH_ENDING):
        return config.AREA_REVIEW
    for path_start, area_name in config.AREA_BY_PATH_START.items():
        if request_path.startswith(path_start):
            return area_name
    return ""
