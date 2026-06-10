"""Prompt Template Engine — renders Jinja2 prompt templates."""

from __future__ import annotations

from typing import Any, Dict


class PromptTemplateEngine:
    """Renders prompt templates with variable substitution using Jinja2."""

    def __init__(self) -> None:
        try:
            from jinja2 import Environment, BaseLoader, select_autoescape
            self._env = Environment(
                loader=BaseLoader(),
                autoescape=select_autoescape(["html"]),
                trim_blocks=True,
                lstrip_blocks=True,
            )
        except ImportError:
            self._env = None

    def render(self, template: str, variables: Dict[str, Any]) -> str:
        if self._env is None:
            # Fallback: simple string replacement
            result = template
            for key, value in variables.items():
                result = result.replace(f"{{{{{key}}}}}", str(value))
            return result
        tpl = self._env.from_string(template)
        return tpl.render(**variables)

    def extract_variables(self, template: str) -> list[str]:
        if self._env is None:
            import re
            return list(set(re.findall(r"\{\{(\w+)\}\}", template)))
        from jinja2 import meta
        ast = self._env.parse(template)
        return sorted(meta.find_undeclared_variables(ast))


# Backwards-compatible alias used by the top-level executable test suite.
TemplateEngine = PromptTemplateEngine