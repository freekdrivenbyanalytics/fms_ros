from collections.abc import Iterable, Sequence

from app.models import Employee


def group_regions_by_shared_employees(
    employees: Sequence[Employee], region_ids: Iterable[int]
) -> list[set[int]]:
    """Connected components of `region_ids`: two regions land in the same
    group whenever at least one employee is scoped to both, directly or
    transitively through a chain of shared employees. This is the only
    grouping rule that can prove no employee crosses a group boundary - see
    add-parallel-region-solving's design.md.

    A region with no employee connecting it to any other in-scope region
    ends up alone in its own single-element group.
    """
    region_id_set = set(region_ids)
    adjacency: dict[int, set[int]] = {region_id: set() for region_id in region_id_set}
    for employee in employees:
        employee_region_ids = {region.id for region in employee.regions} & region_id_set
        for region_id in employee_region_ids:
            adjacency[region_id].update(employee_region_ids - {region_id})

    visited: set[int] = set()
    groups: list[set[int]] = []
    for start in region_id_set:
        if start in visited:
            continue
        group: set[int] = set()
        stack = [start]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            group.add(node)
            stack.extend(adjacency[node] - visited)
        groups.append(group)
    return groups
