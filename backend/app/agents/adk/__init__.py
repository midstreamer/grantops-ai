"""
Google ADK (Agent Development Kit) integration for GrantOps.

This package complements the deterministic internal orchestrator in
:mod:`app.agents.grantops_orchestrator`. It composes ADK ``BaseAgent`` steps that
wrap the same backing services (see :mod:`app.agents.adk.grantops_tools`).

Modules use the ``agents/adk/`` namespace so they do not replace the internal
``app.agents.research_profile_agent`` (and similar) modules.
"""

