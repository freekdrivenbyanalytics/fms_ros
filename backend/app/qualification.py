from app.models import ContractLine


def required_skill_ids(contract_line: ContractLine) -> set[int]:
    """The union of skill ids required by every product a contract line requires."""
    return {
        skill.id for product in contract_line.required_products for skill in product.skills
    }
