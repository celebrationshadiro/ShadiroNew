"""
Advanced ETA and routing system using Google Maps Distance Matrix API.

Features:
- Real-time traffic-aware ETA
- Route optimization
- Intelligent rerouting
- Fallback to straight-line distance
- Redis caching for performance
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import aiohttp
import redis.asyncio as redis

logger = logging.getLogger(__name__)

REDIS_CACHE_ETA = "delivery:eta:{from_lat}_{from_lng}_{to_lat}_{to_lng}"
CACHE_TTL_MINUTES = 30

# Google Maps error handling
MAPS_UNAVAILABLE_FALLBACK_MULTIPLIER = 1.5  # 50% extra time estimate


class ETACalculationService:
    """
    Real-time ETA calculation with traffic awareness.
    """

    def __init__(
        self,
        google_maps_api_key: str,
        redis_client: Optional[redis.Redis] = None,
    ):
        self.api_key = google_maps_api_key
        self.redis = redis_client
        self.session: Optional[aiohttp.ClientSession] = None

    async def connect(self) -> None:
        """Initialize HTTP session."""
        self.session = aiohttp.ClientSession()

    async def disconnect(self) -> None:
        """Cleanup session."""
        if self.session:
            await self.session.close()

    def _get_cache_key(self, from_lat: float, from_lng: float, to_lat: float, to_lng: float) -> str:
        """Generate cache key for ETA."""
        key_str = f"{from_lat}_{from_lng}_{to_lat}_{to_lng}"
        return f"delivery:eta:{hashlib.md5(key_str.encode()).hexdigest()}"

    async def _get_cached_eta(self, cache_key: str) -> Optional[dict[str, Any]]:
        """Get cached ETA if available."""
        if not self.redis:
            return None

        try:
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Cache read failed: {e}")

        return None

    async def _cache_eta(
        self,
        cache_key: str,
        eta_data: dict[str, Any],
        ttl_minutes: int = CACHE_TTL_MINUTES,
    ) -> None:
        """Cache ETA result."""
        if not self.redis:
            return

        try:
            await self.redis.setex(
                cache_key,
                ttl_minutes * 60,
                json.dumps(eta_data),
            )
        except Exception as e:
            logger.error(f"Cache write failed: {e}")

    async def calculate_eta(
        self,
        from_lat: float,
        from_lng: float,
        to_lat: float,
        to_lng: float,
        *,
        current_time: Optional[datetime] = None,
        use_traffic: bool = True,
        return_cached: bool = True,
    ) -> dict[str, Any]:
        """
        Calculate ETA using Google Maps Distance Matrix API.
        
        Args:
            from_lat, from_lng: Origin coordinates
            to_lat, to_lng: Destination coordinates
            current_time: Time to calculate for (defaults to now)
            use_traffic: Include traffic conditions
            return_cached: Return cached result if available
            
        Returns:
            {
                'distance_km': float,
                'duration_minutes': float,
                'duration_in_traffic_minutes': float,
                'traffic_level': str ('low', 'moderate', 'heavy'),
                'cached': bool,
                'calculated_at': str,
            }
        """
        current_time = current_time or datetime.now(timezone.utc)
        cache_key = self._get_cache_key(from_lat, from_lng, to_lat, to_lng)

        # Check cache first
        if return_cached:
            cached = await self._get_cached_eta(cache_key)
            if cached:
                cached["cached"] = True
                return cached

        try:
            if not self.session:
                await self.connect()

            # Call Google Maps Distance Matrix API
            params = {
                "origins": f"{from_lat},{from_lng}",
                "destinations": f"{to_lat},{to_lng}",
                "key": self.api_key,
                "departure_time": int(current_time.timestamp()) if use_traffic else "now",
            }

            async with self.session.get(
                "https://maps.googleapis.com/maps/api/distancematrix/json",
                params=params,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json()

            if data.get("status") != "OK":
                logger.warning(f"Google Maps API error: {data.get('status')}")
                return await self._fallback_eta(from_lat, from_lng, to_lat, to_lng, current_time)

            # Extract results
            row = data.get("rows", [{}])[0]
            element = row.get("elements", [{}])[0]

            if element.get("status") != "OK":
                return await self._fallback_eta(from_lat, from_lng, to_lat, to_lng, current_time)

            distance_m = element.get("distance", {}).get("value", 0)
            duration_s = element.get("duration", {}).get("value", 0)
            duration_traffic_s = element.get("duration_in_traffic", {}).get("value", duration_s)

            distance_km = distance_m / 1000.0
            duration_minutes = duration_s / 60.0
            duration_traffic_minutes = duration_traffic_s / 60.0

            # Determine traffic level
            traffic_ratio = duration_traffic_minutes / max(1, duration_minutes)
            if traffic_ratio > 1.5:
                traffic_level = "heavy"
            elif traffic_ratio > 1.2:
                traffic_level = "moderate"
            else:
                traffic_level = "low"

            result = {
                "distance_km": round(distance_km, 2),
                "duration_minutes": round(duration_minutes, 1),
                "duration_in_traffic_minutes": round(duration_traffic_minutes, 1),
                "traffic_level": traffic_level,
                "cached": False,
                "calculated_at": current_time.isoformat(),
            }

            # Cache result
            await self._cache_eta(cache_key, result)
            return result

        except asyncio.TimeoutError:
            logger.warning("Google Maps API timeout")
            return await self._fallback_eta(from_lat, from_lng, to_lat, to_lng, current_time)
        except Exception as e:
            logger.error(f"ETA calculation error: {e}")
            return await self._fallback_eta(from_lat, from_lng, to_lat, to_lng, current_time)

    async def _fallback_eta(
        self,
        from_lat: float,
        from_lng: float,
        to_lat: float,
        to_lng: float,
        current_time: datetime,
    ) -> dict[str, Any]:
        """
        Fallback ETA calculation using straight-line distance.
        
        Assumes average speed of 25 km/h in Indian urban conditions.
        """
        from shadiro_delivery_network.assignment_engine import haversine_km

        distance_km = haversine_km(from_lat, from_lng, to_lat, to_lng)
        
        # Average urban delivery speed in India: 25 km/h
        avg_speed_kmh = 25.0
        duration_minutes = (distance_km / avg_speed_kmh) * 60

        return {
            "distance_km": round(distance_km, 2),
            "duration_minutes": round(duration_minutes, 1),
            "duration_in_traffic_minutes": round(duration_minutes * MAPS_UNAVAILABLE_FALLBACK_MULTIPLIER, 1),
            "traffic_level": "unknown",
            "cached": False,
            "calculated_at": current_time.isoformat(),
            "method": "fallback_straight_line",
        }

    async def batch_calculate_eta(
        self,
        origins: list[tuple[float, float]],
        destinations: list[tuple[float, float]],
    ) -> dict[str, dict[str, Any]]:
        """
        Calculate ETAs for multiple origin-destination pairs.
        
        Returns dict keyed by "{origin_idx}_{dest_idx}"
        """
        results = {}
        
        # Run in parallel
        tasks = []
        for i, (o_lat, o_lng) in enumerate(origins):
            for j, (d_lat, d_lng) in enumerate(destinations):
                task = self.calculate_eta(o_lat, o_lng, d_lat, d_lng)
                tasks.append((i, j, task))

        eta_results = await asyncio.gather(*[t[2] for t in tasks])

        for (i, j, _), eta in zip(tasks, eta_results):
            results[f"{i}_{j}"] = eta

        return results

    async def optimize_route(
        self,
        deliveries: list[dict[str, tuple[float, float]]],
    ) -> list[dict[str, Any]]:
        """
        Optimize delivery route to minimize total time.
        
        Simple nearest-neighbor algorithm (use TSP solver for larger routes).
        
        Args:
            deliveries: List of {'id': ..., 'lat': float, 'lng': float}
            
        Returns:
            Optimized delivery order with route details
        """
        if not deliveries:
            return []

        current_idx = 0
        remaining = set(range(1, len(deliveries)))
        route = [deliveries[0]]
        total_time_minutes = 0.0

        while remaining:
            current_location = route[-1]
            nearest_idx = None
            nearest_eta = None

            # Find nearest unvisited
            for candidate_idx in remaining:
                candidate = deliveries[candidate_idx]
                eta = await self.calculate_eta(
                    current_location["lat"],
                    current_location["lng"],
                    candidate["lat"],
                    candidate["lng"],
                )
                
                if nearest_eta is None or eta["duration_in_traffic_minutes"] < nearest_eta["duration_in_traffic_minutes"]:
                    nearest_idx = candidate_idx
                    nearest_eta = eta

            if nearest_idx is not None:
                route.append({
                    **deliveries[nearest_idx],
                    "from_eta": nearest_eta,
                })
                total_time_minutes += nearest_eta["duration_in_traffic_minutes"]
                remaining.remove(nearest_idx)

        return {
            "route": route,
            "total_time_minutes": round(total_time_minutes, 1),
            "total_distance_km": sum(d.get("from_eta", {}).get("distance_km", 0) for d in route[1:]),
        }
