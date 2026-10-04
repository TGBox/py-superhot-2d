"""Mathematical and geometric utilities for 2D physics, raycasting, and collisions."""

from __future__ import annotations
import math
from typing import Tuple, List, Optional
import pygame

Vec2 = pygame.Vector2


def distance(p1: Vec2, p2: Vec2) -> float:
    """Euclidean distance between two 2D points."""
    return p1.distance_to(p2)


def clamp(val: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min_val and max_val."""
    return max(min_val, min(max_val, val))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b by factor t."""
    return a + (b - a) * clamp(t, 0.0, 1.0)


def line_segment_intersection(
    p1: Vec2, p2: Vec2, p3: Vec2, p4: Vec2
) -> Optional[Tuple[Vec2, float]]:
    """
    Find intersection between segment (p1->p2) and segment (p3->p4).
    Returns (intersection_point, t) where t is the fractional distance along p1->p2 (0 to 1).
    """
    d1 = p2 - p1
    d2 = p4 - p3

    denom = d1.x * d2.y - d1.y * d2.x
    if abs(denom) < 1e-7:
        return None  # Parallel or collinear

    diff = p3 - p1
    t = (diff.x * d2.y - diff.y * d2.x) / denom
    u = (diff.x * d1.y - diff.y * d1.x) / denom

    if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
        return p1 + d1 * t, t
    return None


def ray_cast_rect(
    start: Vec2, end: Vec2, rect: pygame.Rect
) -> Optional[Tuple[Vec2, float, Vec2]]:
    """
    Cast a ray from start to end against an axis-aligned rectangle.
    Returns (hit_point, t, hit_normal) or None if no hit within the segment.
    """
    tl = Vec2(rect.left, rect.top)
    tr = Vec2(rect.right, rect.top)
    br = Vec2(rect.right, rect.bottom)
    bl = Vec2(rect.left, rect.bottom)

    # 4 segments: top, right, bottom, left
    edges = [
        (tl, tr, Vec2(0, -1)),
        (tr, br, Vec2(1, 0)),
        (br, bl, Vec2(0, 1)),
        (bl, tl, Vec2(-1, 0)),
    ]

    closest_hit = None
    min_t = 1.0

    for e1, e2, normal in edges:
        res = line_segment_intersection(start, end, e1, e2)
        if res is not None:
            pt, t = res
            if t < min_t:
                min_t = t
                closest_hit = (pt, t, normal)

    return closest_hit


def has_line_of_sight(start: Vec2, end: Vec2, walls: List[pygame.Rect]) -> bool:
    """Check if there is a clear direct line of sight between start and end."""
    for wall in walls:
        # Quick bounding box optimization
        if ray_cast_rect(start, end, wall) is not None:
            return False
    return True


def circle_rect_collision(
    circle_pos: Vec2, radius: float, rect: pygame.Rect
) -> Optional[Vec2]:
    """
    Check if a circle intersects an AABB rect.
    If so, returns the minimum penetration/separation vector to push circle out.
    """
    closest_x = clamp(circle_pos.x, float(rect.left), float(rect.right))
    closest_y = clamp(circle_pos.y, float(rect.top), float(rect.bottom))
    closest = Vec2(closest_x, closest_y)

    diff = circle_pos - closest
    dist_sq = diff.length_squared()

    if dist_sq < radius * radius:
        dist = math.sqrt(dist_sq)
        if dist > 1e-5:
            overlap = radius - dist
            return diff.normalize() * overlap
        else:
            # Circle center is exactly inside or on edge, push outward toward closest edge
            left_dist = abs(circle_pos.x - rect.left)
            right_dist = abs(circle_pos.x - rect.right)
            top_dist = abs(circle_pos.y - rect.top)
            bottom_dist = abs(circle_pos.y - rect.bottom)
            min_dist = min(left_dist, right_dist, top_dist, bottom_dist)
            if min_dist == left_dist:
                return Vec2(-(radius + left_dist), 0)
            elif min_dist == right_dist:
                return Vec2(radius + right_dist, 0)
            elif min_dist == top_dist:
                return Vec2(0, -(radius + top_dist))
            else:
                return Vec2(0, radius + bottom_dist)
    return None


def resolve_circle_walls(pos: Vec2, radius: float, walls: List[pygame.Rect]) -> Vec2:
    """Push a circle out of colliding walls iteratively."""
    resolved = Vec2(pos)
    for _ in range(3):  # Multiple iterations for corner resolutions
        collided = False
        for wall in walls:
            push = circle_rect_collision(resolved, radius, wall)
            if push is not None:
                resolved += push
                collided = True
        if not collided:
            break
    return resolved


def cast_vision_cone_polygon(
    origin: Vec2,
    facing_angle: float,
    fov_deg: float,
    max_range: float,
    walls: List[pygame.Rect],
    num_rays: int = 24,
) -> List[Tuple[float, float]]:
    """
    Cast multiple rays across a field of view arc and return a closed polygon.
    Ray hits are truncated by walls.
    """
    fov_rad = math.radians(fov_deg)
    start_ang = facing_angle - fov_rad / 2.0
    end_ang = facing_angle + fov_rad / 2.0

    poly_pts: List[Tuple[float, float]] = [(origin.x, origin.y)]

    for i in range(num_rays + 1):
        ang = start_ang + (end_ang - start_ang) * (i / num_rays)
        dir_vec = Vec2(math.cos(ang), math.sin(ang))
        ray_end = origin + dir_vec * max_range

        closest_pt = ray_end
        min_t = 1.0

        for wall in walls:
            hit = ray_cast_rect(origin, ray_end, wall)
            if hit is not None:
                hit_pt, t, _ = hit
                if t < min_t:
                    min_t = t
                    closest_pt = hit_pt

        poly_pts.append((closest_pt.x, closest_pt.y))

    return poly_pts

