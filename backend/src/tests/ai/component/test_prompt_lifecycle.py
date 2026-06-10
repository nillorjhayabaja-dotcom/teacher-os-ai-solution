"""Component tests for Prompt Registry lifecycle."""

import pytest
from uuid import uuid4

from backend.src.infrastructure.ai.prompts.prompt_registry import PromptRegistry
from backend.src.infrastructure.ai.prompts.template_engine import PromptTemplateEngine


class TestPromptRegistry:
    @pytest.mark.asyncio
    async def test_create_and_list_prompts(self):
        registry = PromptRegistry()
        await registry.create_prompt(
            name="Lesson Plan System",
            description="System prompt for lesson planning agent",
            category="system",
            agent_kind="lesson_planning",
        )
        await registry.create_prompt(
            name="Domain Instructions",
            description="Domain-specific instructions",
            category="domain",
        )
        prompts = await registry.list_prompts()
        assert len(prompts) >= 2
        names = [p["name"] for p in prompts]
        assert "Lesson Plan System" in names
        assert "Domain Instructions" in names

    @pytest.mark.asyncio
    async def test_get_nonexistent_prompt(self):
        registry = PromptRegistry()
        result = await registry.get_prompt(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_active_version_empty(self):
        registry = PromptRegistry()
        result = await registry.get_active_version("nonexistent", "system")
        assert result is None

    @pytest.mark.asyncio
    async def test_create_version_and_retrieve(self):
        registry = PromptRegistry()
        version = await registry.create_version(
            prompt_id=uuid4(),
            system_prompt="You are a teacher assistant.",
            user_template="Help with {{ topic }}",
            variables=["topic"],
        )
        assert version["version_number"] >= 1
        assert "teacher assistant" in version["system_prompt"]


class TestPromptTemplateEngine:
    def test_render_simple(self):
        engine = PromptTemplateEngine()
        result = engine.render("Hello {{ name }}!", {"name": "Teacher"})
        assert result == "Hello Teacher!"

    def test_render_with_condition(self):
        engine = PromptTemplateEngine()
        template = "{% if grade %}Grade: {{ grade }}{% endif %}"
        result = engine.render(template, {"grade": "3"})
        assert result == "Grade: 3"

    def test_render_with_loop(self):
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

    def test_render_with_condition_false(self):
        engine = PromptTemplateEngine()
        template = "{% if show_data %}Data: {{ value }}{% else %}No data{% endif %}"
        result = engine.render(template, {"show_data": False, "value": "test"})
        assert result.strip() == "No data"

    def test_extract_variables_complex(self):
        engine = PromptTemplateEngine()
        template = "{% for item in items %}{{ item.name }}: {{ item.value }}\n{% endfor %}"
        vars_found = engine.extract_variables(template)
        assert "items" in vars_found