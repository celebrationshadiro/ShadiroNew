"""Shadiro Smart Delivery Network — loosely coupled logistics modules.

Subpackages expose domain services consumed only via `routers/delivery_network.py`
and optional background workers. Vendor/grocery modules should call delivery APIs,
not import internal service classes directly.
"""

from shadiro_delivery_network.realtime_hub import DeliveryRealtimeHub

__all__ = ["DeliveryRealtimeHub"]
