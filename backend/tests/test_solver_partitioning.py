from app.solver_partitioning import group_regions_by_shared_employees


class _Region:
    def __init__(self, id: int) -> None:
        self.id = id


class _Employee:
    def __init__(self, id: int, region_ids: list[int]) -> None:
        self.id = id
        self.regions = [_Region(region_id) for region_id in region_ids]


def test_disjoint_regions_produce_separate_groups() -> None:
    employees = [_Employee(1, [1]), _Employee(2, [2])]

    groups = group_regions_by_shared_employees(employees, {1, 2})

    assert sorted(groups, key=min) == [{1}, {2}]


def test_multi_region_employee_merges_their_regions_into_one_group() -> None:
    employees = [_Employee(1, [1, 2]), _Employee(2, [3])]

    groups = group_regions_by_shared_employees(employees, {1, 2, 3})

    assert sorted(groups, key=min) == [{1, 2}, {3}]


def test_chain_of_shared_employees_transitively_merges_regions() -> None:
    # Employee 1 links regions 1-2, employee 2 links regions 2-3: no single
    # employee is scoped to both 1 and 3, but the chain through region 2
    # must still merge all three into one group.
    employees = [
        _Employee(1, [1, 2]),
        _Employee(2, [2, 3]),
        _Employee(3, [4]),
    ]

    groups = group_regions_by_shared_employees(employees, {1, 2, 3, 4})

    assert sorted(groups, key=min) == [{1, 2, 3}, {4}]


def test_region_with_no_scoped_employee_stands_alone() -> None:
    groups = group_regions_by_shared_employees([], {5})

    assert groups == [{5}]


def test_employees_scoped_outside_region_ids_are_ignored() -> None:
    # Employee 1 shares regions 1 and 9, but 9 isn't in scope for this run,
    # so it must not pull in or otherwise affect the grouping of region 1.
    employees = [_Employee(1, [1, 9])]

    groups = group_regions_by_shared_employees(employees, {1, 2})

    assert sorted(groups, key=min) == [{1}, {2}]
