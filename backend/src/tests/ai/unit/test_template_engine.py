"""Unit tests for Prompt Template Engine."""

import pytest
from backend.src.infrastructure.ai.prompts.template_engine import PromptTemplateEngine


class TestPromptTemplateEngine:
    def test_render_simple(self):
        engine = PromptTemplateEngine()
        result = engine.render("Hello {{ name }}!", {"name": "Teacher"})
        assert result == "Hello Teacher!"

    def test_render_with_conditionals(self):
        engine = PromptTemplateEngine()
        template = "{% if grade %}Grade: {{ grade }}{% endif %}"
        result = engine.render(template, {"grade": "3"})
        assert result == "Grade: 3"

    def test_render_with_loops(self):
        engine = PromptTemplateEngine()
        template = "{% for obj in objectives %}- {{ obj }}\n{% endfor %}"
        result = engine.render(template, {"objectives": ["Obj1", "Obj2"]})
        assert "- Obj1" in result
        assert "- Obj2" in result

    def test_extract_variables(self):
        engine = PromptTemplateEngine()
        vars_found = engine.extract_variables("Hello {{ name }}, grade {{ grade_level }}")
        assert "name" in vars_found
        assert "grade_level" in vars_found

    def test_empty_template(self):
        engine = PromptTemplateEngine()
        assert engine.render("", {}) == ""

    def test_missing_variable_default(self):
        engine = PromptTemplateEngine()
        result = engine.render("Value: {{ missing }}", {})
        assert "Value: " in result