"""
Checks all monitored nodes in parallel:
  • Port is set  →  non-blocking TCP connect via asyncio.open_connection
  • No port      →  ICMP echo via icmplib (unprivileged UDP mode, no root needed)

State-change detection writes a StatusLog row and emits rich Loguru output:
  SUCCESS  node recovered   (any → ONLINE)
  WARNING  node went down   (ONLINE → OFFLINE)
  INFO     status unchanged
  ERROR    unexpected exception during an individual check
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from icmplib import async_ping
from loguru import logger
from sqlalchemy import select

from app.config import settings
from app.core.database import AsyncSessionLocal
from app.models.node import Node, NodeStatus
from app.models.status_log import StatusLog


# ─── Per-node result ─────────────────────────────────────────────────────────


@dataclass(slots=True)
class CheckResult:
    node_id: int
    address: str
    status: NodeStatus
    latency_ms: float | None  # None when unreachable


# ─── Check strategies ────────────────────────────────────────────────────────


async def _tcp_check(
    address: str, port: int, timeout: float
) -> tuple[NodeStatus, float | None]:
    """Non-blocking TCP connect check.  Returns (status, latency_ms)."""
    t0 = time.perf_counter()
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(address, port),
            timeout=timeout,
        )
        latency = round((time.perf_counter() - t0) * 1000, 2)
        writer.close()
        await writer.wait_closed()
        return NodeStatus.ONLINE, latency
    except (OSError, asyncio.TimeoutError, ConnectionRefusedError):
        return NodeStatus.OFFLINE, None


async def _icmp_check(
    address: str, timeout: float
) -> tuple[NodeStatus, float | None]:
    """ICMP echo check (unprivileged UDP mode — no root/admin required)."""
    try:
        host = await async_ping(
            address,
            count=1,
            timeout=timeout,
            privileged=False,
        )
        if host.is_alive:
            return NodeStatus.ONLINE, round(host.avg_rtt, 2)
        return NodeStatus.OFFLINE, None
    except Exception as exc:
        logger.error("ICMP check failed for {!r}: {}", address, exc)
        return NodeStatus.OFFLINE, None


async def _check_node(node: Node, timeout: float) -> CheckResult:
    """Dispatch to the correct strategy and wrap any unexpected exceptions."""
    try:
        if node.port is not None:
            status, latency = await _tcp_check(node.address, node.port, timeout)
        else:
            status, latency = await _icmp_check(node.address, timeout)
    except Exception as exc:
        logger.error(
            "Unexpected error checking node {} ({!r}): {}",
            node.id,
            node.address,
            exc,
        )
        status, latency = NodeStatus.OFFLINE, None

    return CheckResult(
        node_id=node.id,
        address=node.address,
        status=status,
        latency_ms=latency,
    )


# ─── Main entry-point ────────────────────────────────────────────────────────


async def run_checks() -> None:
    """
    Fetch all nodes, run checks in parallel with asyncio.gather,
    persist results, and emit state-change logs.

    Called by the APScheduler background job (Phase 3).
    """
    async with AsyncSessionLocal() as session:
        rows = await session.execute(select(Node))
        nodes: list[Node] = list(rows.scalars().all())

    if not nodes:
        logger.debug("Checker: no nodes configured — skipping cycle.")
        return

    timeout = settings.monitoring_timeout_seconds
    logger.debug("Checker: starting cycle for {} node(s).", len(nodes))

    # Run all node checks concurrently.
    results: list[CheckResult] = await asyncio.gather(
        *[_check_node(n, timeout) for n in nodes]
    )

    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as session:
        for res in results:
            node = await session.get(Node, res.node_id)
            if node is None:
                # Node was deleted between the fetch and the persist step.
                continue

            old_status = NodeStatus(node.last_status)
            new_status = res.status

            # ── Persist updated fields ────────────────────────────────────
            node.last_status = new_status.value
            node.last_latency = res.latency_ms
            node.last_check_at = now

            # ── State-change detection ────────────────────────────────────
            if old_status != new_status:
                session.add(
                    StatusLog(
                        node_id=node.id,
                        old_status=old_status.value,
                        new_status=new_status.value,
                    )
                )
                if new_status == NodeStatus.ONLINE:
                    logger.success(
                        "[{}] recovered  {} → {}  (latency: {} ms)",
                        res.address,
                        old_status.value,
                        new_status.value,
                        res.latency_ms,
                    )
                else:
                    logger.warning(
                        "[{}] went down  {} → {}",
                        res.address,
                        old_status.value,
                        new_status.value,
                    )
            else:
                logger.info(
                    "[{}] {}  (latency: {} ms)",
                    res.address,
                    new_status.value,
                    res.latency_ms,
                )

        await session.commit()

    logger.debug("Checker: cycle complete.")
