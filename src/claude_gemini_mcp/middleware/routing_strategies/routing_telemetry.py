#!/usr/bin/env python3
"""
Routing Telemetry - Comprehensive analytics and monitoring for routing decisions.

This module provides advanced telemetry, analytics, and monitoring capabilities
for the routing system, tracking routing decisions, performance patterns,
cost optimization effectiveness, and system health metrics.

Features:
- Real-time routing decision analytics
- Performance trend analysis
- Cost optimization tracking
- Provider health monitoring
- Routing strategy effectiveness metrics
- Detailed logging and reporting
- Alert system for routing anomalies
"""

import logging
import time
import json
from typing import Dict, Any, List, Optional, NamedTuple, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RoutingDecisionType(Enum):
    """Types of routing decisions"""
    SCENARIO_BASED = "scenario_based"
    PERFORMANCE_OPTIMIZED = "performance_optimized"
    COST_OPTIMIZED = "cost_optimized"
    TOKEN_AWARE = "token_aware"
    FALLBACK = "fallback"
    MANUAL_OVERRIDE = "manual_override"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class RoutingDecision:
    """Record of a routing decision"""
    timestamp: float
    request_id: str
    decision_type: RoutingDecisionType
    selected_provider: str
    selected_model: str
    routing_reason: str
    context: Dict[str, Any]
    alternatives_considered: List[str]
    decision_latency_ms: float
    estimated_cost: Optional[float] = None
    estimated_response_time: Optional[float] = None
    quality_score: Optional[float] = None


@dataclass
class PerformanceRecord:
    """Record of actual performance vs predictions"""
    timestamp: float
    request_id: str
    provider: str
    model: str
    actual_response_time: float
    actual_cost: Optional[float]
    actual_quality: Optional[float]
    success: bool
    error_message: Optional[str]
    predicted_response_time: Optional[float]
    predicted_cost: Optional[float]
    prediction_accuracy: Dict[str, float]


@dataclass
class RoutingAlert:
    """Routing system alert"""
    timestamp: float
    severity: AlertSeverity
    category: str
    message: str
    details: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[float] = None


class RoutingTelemetry:
    """Comprehensive telemetry and analytics for routing decisions

    This class tracks routing decisions, performance outcomes, cost effectiveness,
    and provides analytics and alerting capabilities for the routing system.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize routing telemetry

        Args:
            config: Telemetry configuration options
        """
        self.config = config or {}
        self.lock = threading.Lock()

        # Configuration
        self.max_records = self.config.get("max_records", 10000)
        self.analytics_window_hours = self.config.get("analytics_window_hours", 24)
        self.enable_detailed_logging = self.config.get("enable_detailed_logging", True)
        self.alert_thresholds = self.config.get("alert_thresholds", {
            "success_rate_warning": 0.90,
            "success_rate_critical": 0.80,
            "response_time_warning": 15.0,
            "response_time_critical": 30.0,
            "cost_increase_warning": 1.5,  # 50% increase
            "cost_increase_critical": 2.0   # 100% increase
        })

        # Data storage
        self.routing_decisions: deque = deque(maxlen=self.max_records)
        self.performance_records: deque = deque(maxlen=self.max_records)
        self.alerts: deque = deque(maxlen=1000)

        # Analytics cache
        self._analytics_cache: Dict[str, Any] = {}
        self._cache_expiry: float = 0
        self._cache_duration = 300  # 5 minutes

        # Statistics
        self.stats = {
            "total_routing_decisions": 0,
            "total_requests": 0,
            "routing_decision_counts": defaultdict(int),
            "provider_usage_counts": defaultdict(int),
            "model_usage_counts": defaultdict(int),
            "success_rates": defaultdict(list),
            "response_times": defaultdict(list),
            "costs": defaultdict(list)
        }

        logger.info("Initialized routing telemetry system")

    def record_routing_decision(
        self,
        request_id: str,
        decision_type: RoutingDecisionType,
        selected_provider: str,
        selected_model: str,
        routing_reason: str,
        context: Dict[str, Any],
        alternatives_considered: List[str],
        decision_latency_ms: float,
        estimated_cost: Optional[float] = None,
        estimated_response_time: Optional[float] = None,
        quality_score: Optional[float] = None
    ) -> None:
        """Record a routing decision

        Args:
            request_id: Unique request identifier
            decision_type: Type of routing decision made
            selected_provider: Selected provider name
            selected_model: Selected model name
            routing_reason: Explanation for the routing decision
            context: Request context that influenced the decision
            alternatives_considered: List of alternative providers/models considered
            decision_latency_ms: Time taken to make routing decision in milliseconds
            estimated_cost: Estimated cost for the request
            estimated_response_time: Estimated response time
            quality_score: Expected quality score
        """
        with self.lock:
            decision = RoutingDecision(
                timestamp=time.time(),
                request_id=request_id,
                decision_type=decision_type,
                selected_provider=selected_provider,
                selected_model=selected_model,
                routing_reason=routing_reason,
                context=context.copy(),
                alternatives_considered=alternatives_considered.copy(),
                decision_latency_ms=decision_latency_ms,
                estimated_cost=estimated_cost,
                estimated_response_time=estimated_response_time,
                quality_score=quality_score
            )

            self.routing_decisions.append(decision)

            # Update statistics
            self.stats["total_routing_decisions"] += 1
            self.stats["routing_decision_counts"][decision_type.value] += 1
            self.stats["provider_usage_counts"][selected_provider] += 1
            self.stats["model_usage_counts"][f"{selected_provider}/{selected_model}"] += 1

            # Clear analytics cache
            self._clear_analytics_cache()

            if self.enable_detailed_logging:
                logger.info(f"Routing decision recorded: {request_id} -> {selected_provider}/{selected_model} "
                           f"({decision_type.value}) - {routing_reason}")

    def record_performance_outcome(
        self,
        request_id: str,
        provider: str,
        model: str,
        actual_response_time: float,
        success: bool,
        actual_cost: Optional[float] = None,
        actual_quality: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Record actual performance outcome for a request

        Args:
            request_id: Request identifier
            provider: Provider used
            model: Model used
            actual_response_time: Actual response time in seconds
            success: Whether the request was successful
            actual_cost: Actual cost incurred
            actual_quality: Actual quality achieved
            error_message: Error message if request failed
        """
        with self.lock:
            # Find corresponding routing decision
            routing_decision = None
            for decision in reversed(self.routing_decisions):
                if decision.request_id == request_id:
                    routing_decision = decision
                    break

            # Calculate prediction accuracy
            prediction_accuracy = {}
            predicted_response_time = None
            predicted_cost = None

            if routing_decision:
                if routing_decision.estimated_response_time:
                    predicted_response_time = routing_decision.estimated_response_time
                    time_error = abs(actual_response_time - predicted_response_time) / predicted_response_time
                    prediction_accuracy["response_time_accuracy"] = max(0, 1 - time_error)

                if routing_decision.estimated_cost and actual_cost:
                    predicted_cost = routing_decision.estimated_cost
                    cost_error = abs(actual_cost - predicted_cost) / predicted_cost
                    prediction_accuracy["cost_accuracy"] = max(0, 1 - cost_error)

            # Create performance record
            performance_record = PerformanceRecord(
                timestamp=time.time(),
                request_id=request_id,
                provider=provider,
                model=model,
                actual_response_time=actual_response_time,
                actual_cost=actual_cost,
                actual_quality=actual_quality,
                success=success,
                error_message=error_message,
                predicted_response_time=predicted_response_time,
                predicted_cost=predicted_cost,
                prediction_accuracy=prediction_accuracy
            )

            self.performance_records.append(performance_record)

            # Update statistics
            self.stats["total_requests"] += 1
            model_key = f"{provider}/{model}"
            self.stats["success_rates"][model_key].append(1.0 if success else 0.0)
            self.stats["response_times"][model_key].append(actual_response_time)
            if actual_cost:
                self.stats["costs"][model_key].append(actual_cost)

            # Check for alerts
            self._check_performance_alerts(model_key, actual_response_time, success)

            # Clear analytics cache
            self._clear_analytics_cache()

            if self.enable_detailed_logging:
                logger.info(f"Performance outcome recorded: {request_id} - {provider}/{model} "
                           f"({actual_response_time:.2f}s, success={success})")

    def _check_performance_alerts(self, model_key: str, response_time: float, success: bool) -> None:
        """Check for performance-related alerts

        Args:
            model_key: Model identifier
            response_time: Response time in seconds
            success: Whether request was successful
        """
        current_time = time.time()

        # Check response time alerts
        if response_time > self.alert_thresholds["response_time_critical"]:
            self._create_alert(
                AlertSeverity.CRITICAL,
                "performance",
                f"Critical response time: {model_key} took {response_time:.2f}s",
                {"model": model_key, "response_time": response_time, "threshold": self.alert_thresholds["response_time_critical"]}
            )
        elif response_time > self.alert_thresholds["response_time_warning"]:
            self._create_alert(
                AlertSeverity.WARNING,
                "performance",
                f"Slow response time: {model_key} took {response_time:.2f}s",
                {"model": model_key, "response_time": response_time, "threshold": self.alert_thresholds["response_time_warning"]}
            )

        # Check success rate alerts (based on recent performance)
        recent_successes = self.stats["success_rates"][model_key][-10:]  # Last 10 requests
        if len(recent_successes) >= 5:  # Only alert if we have enough data
            success_rate = sum(recent_successes) / len(recent_successes)

            if success_rate < self.alert_thresholds["success_rate_critical"]:
                self._create_alert(
                    AlertSeverity.CRITICAL,
                    "reliability",
                    f"Critical success rate: {model_key} at {success_rate:.1%}",
                    {"model": model_key, "success_rate": success_rate, "threshold": self.alert_thresholds["success_rate_critical"]}
                )
            elif success_rate < self.alert_thresholds["success_rate_warning"]:
                self._create_alert(
                    AlertSeverity.WARNING,
                    "reliability",
                    f"Low success rate: {model_key} at {success_rate:.1%}",
                    {"model": model_key, "success_rate": success_rate, "threshold": self.alert_thresholds["success_rate_warning"]}
                )

    def _create_alert(
        self,
        severity: AlertSeverity,
        category: str,
        message: str,
        details: Dict[str, Any]
    ) -> None:
        """Create a new alert

        Args:
            severity: Alert severity level
            category: Alert category
            message: Alert message
            details: Additional alert details
        """
        alert = RoutingAlert(
            timestamp=time.time(),
            severity=severity,
            category=category,
            message=message,
            details=details
        )

        self.alerts.append(alert)

        # Log the alert
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL
        }[severity]

        logger.log(log_level, f"ROUTING ALERT [{severity.value.upper()}] {category}: {message}")

    def get_routing_analytics(self, hours_back: Optional[int] = None) -> Dict[str, Any]:
        """Get comprehensive routing analytics

        Args:
            hours_back: Number of hours to analyze (default: configured window)

        Returns:
            Dictionary containing routing analytics
        """
        with self.lock:
            # Check cache
            if time.time() < self._cache_expiry and self._analytics_cache:
                return self._analytics_cache.copy()

            hours = hours_back or self.analytics_window_hours
            cutoff_time = time.time() - (hours * 3600)

            # Filter recent data
            recent_decisions = [d for d in self.routing_decisions if d.timestamp > cutoff_time]
            recent_performance = [p for p in self.performance_records if p.timestamp > cutoff_time]

            analytics = {
                "summary": self._generate_summary_analytics(recent_decisions, recent_performance),
                "routing_patterns": self._analyze_routing_patterns(recent_decisions),
                "performance_analysis": self._analyze_performance_patterns(recent_performance),
                "cost_analysis": self._analyze_cost_patterns(recent_performance),
                "prediction_accuracy": self._analyze_prediction_accuracy(recent_performance),
                "provider_comparison": self._compare_providers(recent_performance),
                "alerts_summary": self._summarize_alerts(hours),
                "recommendations": self._generate_recommendations(recent_decisions, recent_performance)
            }

            # Cache results
            self._analytics_cache = analytics
            self._cache_expiry = time.time() + self._cache_duration

            return analytics

    def _generate_summary_analytics(
        self,
        decisions: List[RoutingDecision],
        performance: List[PerformanceRecord]
    ) -> Dict[str, Any]:
        """Generate summary analytics"""
        if not decisions and not performance:
            return {"message": "No data available for analysis"}

        total_requests = len(performance)
        successful_requests = sum(1 for p in performance if p.success)

        return {
            "total_routing_decisions": len(decisions),
            "total_requests_completed": total_requests,
            "overall_success_rate": successful_requests / total_requests if total_requests > 0 else 0,
            "average_response_time": sum(p.actual_response_time for p in performance) / len(performance) if performance else 0,
            "average_decision_latency_ms": sum(d.decision_latency_ms for d in decisions) / len(decisions) if decisions else 0,
            "most_used_provider": self._get_most_used_provider(decisions),
            "most_used_model": self._get_most_used_model(decisions),
            "most_common_decision_type": self._get_most_common_decision_type(decisions)
        }

    def _analyze_routing_patterns(self, decisions: List[RoutingDecision]) -> Dict[str, Any]:
        """Analyze routing decision patterns"""
        if not decisions:
            return {}

        decision_types = defaultdict(int)
        provider_usage = defaultdict(int)
        model_usage = defaultdict(int)
        scenario_routing = defaultdict(lambda: defaultdict(int))

        for decision in decisions:
            decision_types[decision.decision_type.value] += 1
            provider_usage[decision.selected_provider] += 1
            model_usage[f"{decision.selected_provider}/{decision.selected_model}"] += 1

            scenario = decision.context.get("scenario", "unknown")
            scenario_routing[scenario][decision.selected_provider] += 1

        return {
            "decision_type_distribution": dict(decision_types),
            "provider_usage_distribution": dict(provider_usage),
            "model_usage_distribution": dict(model_usage),
            "scenario_based_routing": {k: dict(v) for k, v in scenario_routing.items()}
        }

    def _analyze_performance_patterns(self, performance: List[PerformanceRecord]) -> Dict[str, Any]:
        """Analyze performance patterns"""
        if not performance:
            return {}

        provider_performance = defaultdict(lambda: {"response_times": [], "success_rates": []})

        for record in performance:
            key = f"{record.provider}/{record.model}"
            provider_performance[key]["response_times"].append(record.actual_response_time)
            provider_performance[key]["success_rates"].append(1.0 if record.success else 0.0)

        # Calculate aggregated metrics
        performance_summary = {}
        for model, data in provider_performance.items():
            response_times = data["response_times"]
            success_rates = data["success_rates"]

            performance_summary[model] = {
                "average_response_time": sum(response_times) / len(response_times),
                "median_response_time": sorted(response_times)[len(response_times) // 2],
                "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)],
                "success_rate": sum(success_rates) / len(success_rates),
                "total_requests": len(response_times)
            }

        return performance_summary

    def _analyze_cost_patterns(self, performance: List[PerformanceRecord]) -> Dict[str, Any]:
        """Analyze cost patterns"""
        performance_with_cost = [p for p in performance if p.actual_cost is not None]

        if not performance_with_cost:
            return {"message": "No cost data available"}

        cost_by_model = defaultdict(list)
        for record in performance_with_cost:
            model_key = f"{record.provider}/{record.model}"
            cost_by_model[model_key].append(record.actual_cost)

        cost_analysis = {}
        total_cost = sum(p.actual_cost for p in performance_with_cost)

        for model, costs in cost_by_model.items():
            model_total = sum(costs)
            cost_analysis[model] = {
                "total_cost": model_total,
                "average_cost": model_total / len(costs),
                "cost_share": model_total / total_cost if total_cost > 0 else 0,
                "request_count": len(costs)
            }

        return {
            "total_cost": total_cost,
            "cost_by_model": cost_analysis,
            "most_expensive_model": max(cost_analysis.keys(), key=lambda k: cost_analysis[k]["average_cost"]) if cost_analysis else None,
            "most_cost_effective_model": min(cost_analysis.keys(), key=lambda k: cost_analysis[k]["average_cost"]) if cost_analysis else None
        }

    def _analyze_prediction_accuracy(self, performance: List[PerformanceRecord]) -> Dict[str, Any]:
        """Analyze prediction accuracy"""
        predictions_with_data = [p for p in performance if p.prediction_accuracy]

        if not predictions_with_data:
            return {"message": "No prediction data available"}

        response_time_accuracies = []
        cost_accuracies = []

        for record in predictions_with_data:
            if "response_time_accuracy" in record.prediction_accuracy:
                response_time_accuracies.append(record.prediction_accuracy["response_time_accuracy"])
            if "cost_accuracy" in record.prediction_accuracy:
                cost_accuracies.append(record.prediction_accuracy["cost_accuracy"])

        return {
            "response_time_prediction_accuracy": {
                "average": sum(response_time_accuracies) / len(response_time_accuracies) if response_time_accuracies else 0,
                "samples": len(response_time_accuracies)
            },
            "cost_prediction_accuracy": {
                "average": sum(cost_accuracies) / len(cost_accuracies) if cost_accuracies else 0,
                "samples": len(cost_accuracies)
            }
        }

    def _compare_providers(self, performance: List[PerformanceRecord]) -> Dict[str, Any]:
        """Compare provider performance"""
        provider_stats = defaultdict(lambda: {
            "response_times": [],
            "costs": [],
            "successes": 0,
            "failures": 0
        })

        for record in performance:
            stats = provider_stats[record.provider]
            stats["response_times"].append(record.actual_response_time)
            if record.actual_cost:
                stats["costs"].append(record.actual_cost)
            if record.success:
                stats["successes"] += 1
            else:
                stats["failures"] += 1

        comparison = {}
        for provider, stats in provider_stats.items():
            total_requests = stats["successes"] + stats["failures"]
            comparison[provider] = {
                "average_response_time": sum(stats["response_times"]) / len(stats["response_times"]) if stats["response_times"] else 0,
                "average_cost": sum(stats["costs"]) / len(stats["costs"]) if stats["costs"] else 0,
                "success_rate": stats["successes"] / total_requests if total_requests > 0 else 0,
                "total_requests": total_requests
            }

        return comparison

    def _summarize_alerts(self, hours_back: int) -> Dict[str, Any]:
        """Summarize recent alerts"""
        cutoff_time = time.time() - (hours_back * 3600)
        recent_alerts = [a for a in self.alerts if a.timestamp > cutoff_time]

        if not recent_alerts:
            return {"message": "No recent alerts"}

        alert_counts = defaultdict(int)
        category_counts = defaultdict(int)
        unresolved_count = 0

        for alert in recent_alerts:
            alert_counts[alert.severity.value] += 1
            category_counts[alert.category] += 1
            if not alert.resolved:
                unresolved_count += 1

        return {
            "total_alerts": len(recent_alerts),
            "unresolved_alerts": unresolved_count,
            "alerts_by_severity": dict(alert_counts),
            "alerts_by_category": dict(category_counts),
            "recent_critical_alerts": [
                {"timestamp": a.timestamp, "message": a.message, "details": a.details}
                for a in recent_alerts if a.severity == AlertSeverity.CRITICAL
            ][-5:]  # Last 5 critical alerts
        }

    def _generate_recommendations(
        self,
        decisions: List[RoutingDecision],
        performance: List[PerformanceRecord]
    ) -> List[str]:
        """Generate recommendations based on analytics"""
        recommendations = []

        if not performance:
            return ["Insufficient data for recommendations"]

        # Analyze success rates
        provider_success_rates = defaultdict(list)
        for record in performance:
            provider_success_rates[record.provider].append(1.0 if record.success else 0.0)

        for provider, success_rates in provider_success_rates.items():
            avg_success_rate = sum(success_rates) / len(success_rates)
            if avg_success_rate < 0.85:
                recommendations.append(f"Consider reducing routing to {provider} (success rate: {avg_success_rate:.1%})")

        # Analyze response times
        model_response_times = defaultdict(list)
        for record in performance:
            model_key = f"{record.provider}/{record.model}"
            model_response_times[model_key].append(record.actual_response_time)

        fast_models = []
        slow_models = []
        for model, times in model_response_times.items():
            avg_time = sum(times) / len(times)
            if avg_time < 5.0:
                fast_models.append((model, avg_time))
            elif avg_time > 20.0:
                slow_models.append((model, avg_time))

        if fast_models:
            fastest = min(fast_models, key=lambda x: x[1])
            recommendations.append(f"Consider prioritizing {fastest[0]} for speed-critical tasks (avg: {fastest[1]:.1f}s)")

        if slow_models:
            slowest = max(slow_models, key=lambda x: x[1])
            recommendations.append(f"Consider alternatives to {slowest[0]} for time-sensitive tasks (avg: {slowest[1]:.1f}s)")

        # Cost recommendations
        costs_by_model = defaultdict(list)
        for record in performance:
            if record.actual_cost:
                model_key = f"{record.provider}/{record.model}"
                costs_by_model[model_key].append(record.actual_cost)

        if costs_by_model:
            cost_effective_models = []
            for model, costs in costs_by_model.items():
                avg_cost = sum(costs) / len(costs)
                cost_effective_models.append((model, avg_cost))

            if cost_effective_models:
                cheapest = min(cost_effective_models, key=lambda x: x[1])
                recommendations.append(f"Consider {cheapest[0]} for cost-sensitive tasks (avg cost: ${cheapest[1]:.4f})")

        return recommendations[:10]  # Limit to top 10 recommendations

    def _get_most_used_provider(self, decisions: List[RoutingDecision]) -> Optional[str]:
        """Get the most frequently used provider"""
        if not decisions:
            return None
        provider_counts = defaultdict(int)
        for decision in decisions:
            provider_counts[decision.selected_provider] += 1
        return max(provider_counts.keys(), key=provider_counts.get)

    def _get_most_used_model(self, decisions: List[RoutingDecision]) -> Optional[str]:
        """Get the most frequently used model"""
        if not decisions:
            return None
        model_counts = defaultdict(int)
        for decision in decisions:
            model_key = f"{decision.selected_provider}/{decision.selected_model}"
            model_counts[model_key] += 1
        return max(model_counts.keys(), key=model_counts.get)

    def _get_most_common_decision_type(self, decisions: List[RoutingDecision]) -> Optional[str]:
        """Get the most common decision type"""
        if not decisions:
            return None
        type_counts = defaultdict(int)
        for decision in decisions:
            type_counts[decision.decision_type.value] += 1
        return max(type_counts.keys(), key=type_counts.get)

    def _clear_analytics_cache(self) -> None:
        """Clear the analytics cache"""
        self._analytics_cache.clear()
        self._cache_expiry = 0

    def export_telemetry_data(
        self,
        format_type: str = "json",
        include_performance: bool = True,
        include_decisions: bool = True,
        include_alerts: bool = True
    ) -> str:
        """Export telemetry data in specified format

        Args:
            format_type: Export format ("json" currently supported)
            include_performance: Include performance records
            include_decisions: Include routing decisions
            include_alerts: Include alerts

        Returns:
            Formatted telemetry data string
        """
        with self.lock:
            export_data = {
                "export_timestamp": time.time(),
                "export_format": format_type,
                "summary": self.stats
            }

            if include_decisions:
                export_data["routing_decisions"] = [
                    asdict(decision) for decision in self.routing_decisions
                ]

            if include_performance:
                export_data["performance_records"] = [
                    asdict(record) for record in self.performance_records
                ]

            if include_alerts:
                export_data["alerts"] = [
                    asdict(alert) for alert in self.alerts
                ]

            if format_type == "json":
                return json.dumps(export_data, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported export format: {format_type}")

    def clear_telemetry_data(self, data_type: Optional[str] = None) -> None:
        """Clear telemetry data

        Args:
            data_type: Type of data to clear ("decisions", "performance", "alerts", or None for all)
        """
        with self.lock:
            if data_type is None or data_type == "all":
                self.routing_decisions.clear()
                self.performance_records.clear()
                self.alerts.clear()
                self.stats = {
                    "total_routing_decisions": 0,
                    "total_requests": 0,
                    "routing_decision_counts": defaultdict(int),
                    "provider_usage_counts": defaultdict(int),
                    "model_usage_counts": defaultdict(int),
                    "success_rates": defaultdict(list),
                    "response_times": defaultdict(list),
                    "costs": defaultdict(list)
                }
                logger.info("Cleared all telemetry data")
            elif data_type == "decisions":
                self.routing_decisions.clear()
                logger.info("Cleared routing decisions")
            elif data_type == "performance":
                self.performance_records.clear()
                logger.info("Cleared performance records")
            elif data_type == "alerts":
                self.alerts.clear()
                logger.info("Cleared alerts")
            else:
                raise ValueError(f"Invalid data type: {data_type}")

            self._clear_analytics_cache()
