"""
Mini capability schema for ultra-light tool discovery
Addresses critique about progressive discovery still being too heavy
"""

import json
import hashlib
from typing import Dict, List, Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()

class MiniCapability(BaseModel):
    """
    Minimal capability descriptor - max 200 tokens
    This is what agents see BEFORE calling discover()
    """
    id: str = Field(description="Unique capability ID")
    name: str = Field(description="Human-readable name, max 20 chars", max_length=20)
    desc: str = Field(description="One-line description, max 50 chars", max_length=50)
    cost: int = Field(description="Estimated tokens to load full schema", ge=0, le=10000)
    tags: List[str] = Field(default_factory=list, description="Search tags", max_items=3)
    sig: Optional[str] = Field(default=None, description="SHA256 signature for verification")

    def sign(self, secret: str) -> None:
        """Sign capability for integrity"""
        content = f"{self.id}{self.name}{self.desc}{self.cost}"
        self.sig = hashlib.sha256(f"{content}{secret}".encode()).hexdigest()[:16]

    def verify(self, secret: str) -> bool:
        """Verify capability signature"""
        if not self.sig:
            return False
        content = f"{self.id}{self.name}{self.desc}{self.cost}"
        expected = hashlib.sha256(f"{content}{secret}".encode()).hexdigest()[:16]
        return self.sig == expected

    def token_estimate(self) -> int:
        """Estimate tokens for this capability descriptor"""
        # Rough estimate: 4 chars = 1 token
        json_str = json.dumps(self.dict(exclude_none=True))
        return len(json_str) // 4

class CapabilityRegistry:
    """
    Ultra-lightweight capability registry
    Entire manifest fits in <200 tokens as requested in critique
    """

    # Pre-computed mini manifests (would be generated at build time)
    CAPABILITIES = {
        "sentry": MiniCapability(
            id="sentry",
            name="Sentry",
            desc="Error tracking: list, analyze, fix",
            cost=500,
            tags=["error", "debug", "monitor"]
        ),
        "github": MiniCapability(
            id="github",
            name="GitHub",
            desc="Code: PR, issues, commits",
            cost=400,
            tags=["code", "git", "pr"]
        ),
        "db": MiniCapability(
            id="db",
            name="Database",
            desc="Query, analyze, optimize SQL",
            cost=300,
            tags=["sql", "data", "query"]
        ),
        "docker": MiniCapability(
            id="docker",
            name="Docker",
            desc="Container: build, run, logs",
            cost=350,
            tags=["container", "deploy"]
        ),
        "aws": MiniCapability(
            id="aws",
            name="AWS",
            desc="Cloud: EC2, S3, Lambda",
            cost=600,
            tags=["cloud", "deploy", "infra"]
        ),
        "metrics": MiniCapability(
            id="metrics",
            name="Metrics",
            desc="Monitor: APM, logs, alerts",
            cost=450,
            tags=["monitor", "apm", "alert"]
        )
    }

    def __init__(self, secret: Optional[str] = None):
        self.secret = secret or "default-secret"
        self.loaded_capabilities: Dict[str, Any] = {}

        # Sign all capabilities
        for cap in self.CAPABILITIES.values():
            cap.sign(self.secret)

        # Pre-compute the entire manifest
        self._compute_manifest()

    def _compute_manifest(self):
        """Pre-compute ultra-compact manifest"""

        # Ultra-compact format to minimize tokens
        self.compact_manifest = {
            "v": 1,  # Version
            "caps": [
                {
                    "i": cap.id,
                    "n": cap.name,
                    "d": cap.desc,
                    "c": cap.cost,
                    "t": cap.tags[0] if cap.tags else ""  # Primary tag only
                }
                for cap in self.CAPABILITIES.values()
            ]
        }

        # Calculate actual token usage
        manifest_json = json.dumps(self.compact_manifest, separators=(',', ':'))
        self.manifest_tokens = len(manifest_json) // 4

        logger.info(
            "manifest_computed",
            capabilities=len(self.CAPABILITIES),
            total_tokens=self.manifest_tokens
        )

    def get_manifest(self) -> Dict[str, Any]:
        """
        Get ultra-light manifest for agent discovery
        This is what agents load FIRST - must be tiny
        """
        return {
            "manifest": self.compact_manifest,
            "tokens": self.manifest_tokens,  # Should be <200
            "help": "Call discover(cap_id) to load specific capability"
        }

    def discover(self, capability_id: str) -> Optional[Dict[str, Any]]:
        """
        Load full capability details ONLY when needed
        This is called AFTER agent decides from manifest
        """

        if capability_id not in self.CAPABILITIES:
            logger.warning("capability_not_found", id=capability_id)
            return None

        # Check if already loaded (cache)
        if capability_id in self.loaded_capabilities:
            logger.info("capability_cache_hit", id=capability_id)
            return self.loaded_capabilities[capability_id]

        # Load full details (this is where tokens are spent)
        cap = self.CAPABILITIES[capability_id]

        # Verify integrity
        if not cap.verify(self.secret):
            logger.error("capability_signature_invalid", id=capability_id)
            return None

        # Load the actual implementation
        full_details = self._load_capability_implementation(capability_id)

        # Cache for session
        self.loaded_capabilities[capability_id] = full_details

        logger.info(
            "capability_loaded",
            id=capability_id,
            tokens_used=cap.cost
        )

        return full_details

    def _load_capability_implementation(self, capability_id: str) -> Dict[str, Any]:
        """Load the actual implementation for a capability"""

        # This would load from files/modules in production
        implementations = {
            "sentry": {
                "functions": [
                    "list_errors(limit=5)",
                    "get_trace(error_id)",
                    "analyze_pattern(timeframe='24h')"
                ],
                "setup": "from integrations.sentry import SentryClient",
                "examples": [
                    "errors = list_errors(5)",
                    "trace = get_trace('12345')",
                    "pattern = analyze_pattern()"
                ]
            },
            "github": {
                "functions": [
                    "create_pr(title, body)",
                    "create_issue(title, body)",
                    "list_commits(branch='main')"
                ],
                "setup": "from integrations.github import GitHubClient",
                "examples": [
                    "pr = create_pr('Fix bug', 'Details...')",
                    "issue = create_issue('Bug report', 'Steps...')"
                ]
            }
            # etc...
        }

        return implementations.get(capability_id, {
            "error": "Implementation not found"
        })

    def search_capabilities(self, query: str) -> List[str]:
        """
        Search capabilities by tags/keywords
        Returns just IDs to minimize tokens
        """

        query_lower = query.lower()
        matches = []

        for cap_id, cap in self.CAPABILITIES.items():
            # Search in name, description, and tags
            searchable = f"{cap.name} {cap.desc} {' '.join(cap.tags)}".lower()

            if query_lower in searchable:
                matches.append(cap_id)

        return matches

    def estimate_total_load(self, capability_ids: List[str]) -> int:
        """Estimate total tokens to load multiple capabilities"""

        total = self.manifest_tokens  # Base manifest

        for cap_id in capability_ids:
            if cap_id in self.CAPABILITIES:
                total += self.CAPABILITIES[cap_id].cost

        return total

    def get_capability_stats(self) -> Dict[str, Any]:
        """Get statistics about capability usage"""

        return {
            "total_capabilities": len(self.CAPABILITIES),
            "manifest_tokens": self.manifest_tokens,
            "loaded_capabilities": list(self.loaded_capabilities.keys()),
            "cache_size": len(self.loaded_capabilities),
            "total_tokens_if_all_loaded": sum(
                cap.cost for cap in self.CAPABILITIES.values()
            )
        }


class CapabilityProtocol:
    """
    Defines the protocol for capability negotiation
    This is how agents and servers agree on what to load
    """

    @staticmethod
    def handshake() -> Dict[str, Any]:
        """
        Initial handshake - returns manifest
        This is the ONLY thing loaded initially
        """
        registry = CapabilityRegistry()
        return {
            "protocol": "mcp-capabilities/v1",
            "manifest": registry.get_manifest(),
            "commands": [
                "discover(capability_id) - Load specific capability",
                "search(query) - Search capabilities",
                "estimate(cap_ids) - Estimate tokens for multiple"
            ]
        }

    @staticmethod
    def negotiate(agent_needs: List[str]) -> Dict[str, Any]:
        """
        Negotiate which capabilities to load based on agent needs
        This optimizes token usage
        """

        registry = CapabilityRegistry()

        # Estimate token cost
        estimated_tokens = registry.estimate_total_load(agent_needs)

        # Determine load strategy
        if estimated_tokens < 1000:
            # Load all requested
            strategy = "load_all"
            capabilities = agent_needs
        elif estimated_tokens < 5000:
            # Load progressively
            strategy = "progressive"
            capabilities = agent_needs[:2]  # Start with first 2
        else:
            # Require explicit confirmation
            strategy = "confirm_required"
            capabilities = []

        return {
            "strategy": strategy,
            "estimated_tokens": estimated_tokens,
            "initial_load": capabilities,
            "deferred": [c for c in agent_needs if c not in capabilities]
        }


# Public API for easy access
def get_mini_manifest() -> Dict[str, Any]:
    """
    Get the ultra-compact capability manifest
    This is the main entry point for benchmarks and external use
    """
    registry = CapabilityRegistry()
    return registry.get_manifest()


# Alias for backward compatibility
CapabilityDetector = CapabilityRegistry