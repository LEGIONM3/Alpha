"""API Intelligence Tools for Alpha OS ToolRegistry."""

from typing import Any, Dict, List, Optional
from alpha.tools.protocol import (
    BaseTool,
    ToolCapability,
    ToolPermission,
    ToolParameter,
    ValidationRule
)
from alpha.api.gateway import APIGateway

class ApiRestRequestTool(BaseTool):
    def __init__(self, gateway: Optional[APIGateway] = None):
        super().__init__(
            name="api_rest_request",
            description="Executes an HTTP REST request (GET, POST, PUT, DELETE, PATCH) with auth, rate limits, and circuit breaker guard.",
            capabilities=[ToolCapability.API],
            permissions=[ToolPermission.API, ToolPermission.NETWORK],
            parameters={
                "method": ToolParameter(name="method", type="string", description="HTTP method e.g. GET, POST.", required=True, enum_values=["GET", "POST", "PUT", "DELETE", "PATCH"]),
                "url": ToolParameter(name="url", type="string", description="Full target URL.", required=True),
                "headers": ToolParameter(name="headers", type="dict", description="Optional HTTP headers.", required=False, default=None),
                "json_body": ToolParameter(name="json_body", type="dict", description="JSON payload dictionary.", required=False, default=None),
                "auth_token": ToolParameter(name="auth_token", type="string", description="Bearer token credentials.", required=False, default=None)
            },
            validation_rules=[
                ValidationRule(rule_type="non_empty", target_field="url", error_message="URL cannot be empty.")
            ]
        )
        self.gateway = gateway or APIGateway()

    def run(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        auth_type = "bearer" if auth_token else None
        return self.gateway.rest_request(
            method=method,
            url=url,
            headers=headers,
            json_body=json_body,
            auth_type=auth_type,
            auth_credentials=auth_token
        )


class ApiGraphQLQueryTool(BaseTool):
    def __init__(self, gateway: Optional[APIGateway] = None):
        super().__init__(
            name="api_graphql_query",
            description="Executes a GraphQL query or mutation against a GraphQL endpoint.",
            capabilities=[ToolCapability.API],
            permissions=[ToolPermission.API, ToolPermission.NETWORK],
            parameters={
                "endpoint_url": ToolParameter(name="endpoint_url", type="string", description="GraphQL server endpoint URL.", required=True),
                "query": ToolParameter(name="query", type="string", description="GraphQL query or mutation document.", required=True),
                "variables": ToolParameter(name="variables", type="dict", description="Optional variables dictionary.", required=False, default=None),
                "auth_token": ToolParameter(name="auth_token", type="string", description="Bearer token.", required=False, default=None)
            },
            validation_rules=[
                ValidationRule(rule_type="non_empty", target_field="query", error_message="GraphQL query cannot be empty.")
            ]
        )
        self.gateway = gateway or APIGateway()

    def run(
        self,
        endpoint_url: str,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        return self.gateway.graphql_query(
            endpoint_url=endpoint_url,
            query=query,
            variables=variables,
            auth_token=auth_token
        )


class ApiWebhookTriggerTool(BaseTool):
    def __init__(self, gateway: Optional[APIGateway] = None):
        super().__init__(
            name="api_webhook_trigger",
            description="Dispatches a signed webhook event to an external listener URL.",
            capabilities=[ToolCapability.API],
            permissions=[ToolPermission.API, ToolPermission.NETWORK],
            parameters={
                "target_url": ToolParameter(name="target_url", type="string", description="Webhook receiver URL.", required=True),
                "event_name": ToolParameter(name="event_name", type="string", description="Name of the webhook event.", required=True),
                "payload": ToolParameter(name="payload", type="dict", description="Payload payload dictionary.", required=True),
                "secret_key": ToolParameter(name="secret_key", type="string", description="HMAC secret key.", required=False, default=None)
            }
        )
        self.gateway = gateway or APIGateway()

    def run(self, target_url: str, event_name: str, payload: Dict[str, Any], secret_key: Optional[str] = None) -> Dict[str, Any]:
        return self.gateway.trigger_webhook(
            target_url=target_url,
            event_name=event_name,
            payload=payload,
            secret_key=secret_key
        )


class ApiCircuitBreakerStatusTool(BaseTool):
    def __init__(self, gateway: Optional[APIGateway] = None):
        super().__init__(
            name="api_circuit_status",
            description="Inspects the current state (CLOSED, OPEN, HALF_OPEN) of API Gateway circuit breakers.",
            capabilities=[ToolCapability.API, ToolCapability.ANALYTICS],
            permissions=[ToolPermission.ANALYTICS],
            parameters={
                "host": ToolParameter(name="host", type="string", description="Optional specific host to inspect.", required=False, default="")
            }
        )
        self.gateway = gateway or APIGateway()

    def run(self, host: str = "") -> Dict[str, Any]:
        return self.gateway.get_circuit_status(host=host if host else None)
