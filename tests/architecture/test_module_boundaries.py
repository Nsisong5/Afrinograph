import ast
from pathlib import Path

import pytest


class DomainImportVisitor(ast.NodeVisitor):
    """AST visitor to check imports inside domain and application modules."""

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self.forbidden_imports = [
            "sqlalchemy",
            "fastapi",
            "httpx",
            "asyncpg",
            "psycopg",
            "pydantic",
        ]
        self.violations: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            for forbidden in self.forbidden_imports:
                if alias.name.startswith(forbidden):
                    self.violations.append(
                        f"{self.filepath}:{node.lineno} - Forbidden import of '{alias.name}' in inner layer."
                    )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            for forbidden in self.forbidden_imports:
                if node.module.startswith(forbidden):
                    self.violations.append(
                        f"{self.filepath}:{node.lineno} - Forbidden import from '{node.module}' in inner layer."
                    )
            # Also check if importing infrastructure
            if "infrastructure" in node.module or node.module.startswith("afrinograph.shared.infrastructure"):
                self.violations.append(
                    f"{self.filepath}:{node.lineno} - Inner layer cannot import infrastructure module '{node.module}'."
                )
        self.generic_visit(node)


@pytest.mark.architecture
def test_domain_and_application_layer_isolation() -> None:
    """Enforce that domain and application layers across all modules do not import forbidden frameworks or infrastructure."""
    src_dir = Path("src/afrinograph")
    if not src_dir.exists():
        pytest.skip("Source directory does not exist yet.")

    violations: list[str] = []

    # Find all domain and application directories
    layer_paths = list(src_dir.glob("**/domain")) + list(src_dir.glob("**/application"))
    for layer_path in layer_paths:
        if layer_path.is_dir():
            for py_file in layer_path.glob("**/*.py"):
                tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
                visitor = DomainImportVisitor(str(py_file))
                visitor.visit(tree)
                violations.extend(visitor.violations)

    assert not violations, "Architecture boundary violations found in domain or application layer:\n" + "\n".join(violations)


@pytest.mark.architecture
def test_architecture_scanner_self_test() -> None:
    """Verify that the AST boundary scanner correctly flags forbidden imports when tested with a synthetic violation."""
    bad_code = "import sqlalchemy\nfrom afrinograph.shared.infrastructure import db\n"
    tree = ast.parse(bad_code)
    visitor = DomainImportVisitor("fake_domain.py")
    visitor.visit(tree)
    
    assert len(visitor.violations) == 2
    assert any("sqlalchemy" in v for v in visitor.violations)
    assert any("infrastructure" in v for v in visitor.violations)
