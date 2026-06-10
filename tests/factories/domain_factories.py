from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

try:
    import factory
    from faker import Faker
except Exception:  # pragma: no cover - allows static import before test dependencies are installed
    factory = None
    Faker = None

fake = Faker() if Faker else None


@dataclass(frozen=True)
class TenantRecord:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    school_id: UUID = field(default_factory=uuid4)
    name: str = "TeacherOS Test Tenant"


@dataclass(frozen=True)
class UserRecord:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    email: str = "teacher@example.test"
    roles: tuple[str, ...] = ("teacher",)
    permissions: tuple[str, ...] = ("lesson.create", "grade.compute")


@dataclass(frozen=True)
class StudentRecord:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    lrn: str = "123456789012"
    first_name: str = "Ana"
    last_name: str = "Santos"
    grade_level: str = "6"
    section: str = "Mabini"


if factory:
    class TenantFactory(factory.Factory):
        class Meta:
            model = TenantRecord

        id = factory.LazyFunction(uuid4)
        organization_id = factory.LazyFunction(uuid4)
        school_id = factory.LazyFunction(uuid4)
        name = factory.LazyFunction(lambda: fake.company())


    class UserFactory(factory.Factory):
        class Meta:
            model = UserRecord

        id = factory.LazyFunction(uuid4)
        tenant_id = factory.LazyFunction(uuid4)
        email = factory.LazyFunction(lambda: fake.unique.email())
        roles = ("teacher",)
        permissions = ("lesson.create", "grade.compute")


    class StudentFactory(factory.Factory):
        class Meta:
            model = StudentRecord

        id = factory.LazyFunction(uuid4)
        tenant_id = factory.LazyFunction(uuid4)
        lrn = factory.LazyFunction(lambda: fake.numerify(text="############"))
        first_name = factory.LazyFunction(lambda: fake.first_name())
        last_name = factory.LazyFunction(lambda: fake.last_name())
        grade_level = "6"
        section = "Mabini"
else:
    TenantFactory = TenantRecord
    UserFactory = UserRecord
    StudentFactory = StudentRecord
