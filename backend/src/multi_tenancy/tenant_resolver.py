"""Simple tenant resolver returning a constant identifier."""


class TenantResolver:
    def resolve(self, request) -> str:  # pragma: no cover
        # In a real implementation this would inspect the request.
        return "default_tenant"


__all__ = ["TenantResolver"]