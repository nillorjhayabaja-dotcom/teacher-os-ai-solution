"""A very small stub of the *punq* dependency‑injection container.

The real library provides a feature‑rich container; for the purposes of this
exercise we only need ``register`` and ``resolve`` to satisfy imports.
"""

class Container:
    def __init__(self) -> None:
        self._registry = {}

    def register(self, interface, implementation, *, singleton: bool = False):
        # Store the implementation or a factory. ``singleton`` flag is ignored
        # in this stub – we always store the callable/value directly.
        self._registry[interface] = implementation

    def resolve(self, interface):
        impl = self._registry.get(interface)
        if impl is None:
            raise KeyError(f"No registration for {interface}")
        # If a class was registered, instantiate it without arguments.
        if isinstance(impl, type):
            return impl()
        return impl
