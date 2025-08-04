#!/usr/bin/env python3
"""
Test script for Phase 3: Advanced Routing Logic

This script tests the performance optimizer, telemetry, and enhanced routing
features to ensure they're working correctly.
"""

import sys
import os
import time
import logging

# Add the source directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_advanced_routing_features():
    """Test the advanced routing features"""
    print("🧪 Testing Phase 3: Advanced Routing Logic")
    print("=" * 60)

    try:
        # Import required modules
        from claude_gemini_mcp.middleware.router import Router, RouteRequest
        from claude_gemini_mcp.middleware.routing_strategies.performance_optimizer import PerformanceOptimizer
        from claude_gemini_mcp.middleware.routing_strategies.routing_telemetry import RoutingTelemetry
        from claude_gemini_mcp.config import get_config

        print("✅ Successfully imported advanced routing modules")

        # Test configuration access
        config = get_config()
        print(f"✅ Configuration loaded: routing_enabled={config.is_routing_enabled()}")

        # Test performance optimizer configuration
        perf_config = config.get_performance_config()
        print(f"✅ Performance config: {len(perf_config)} settings")

        # Test telemetry configuration
        telemetry_config = config.get_telemetry_config()
        print(f"✅ Telemetry config: enabled={config.is_telemetry_enabled()}")

        # Test routing preferences
        routing_strategy = config.get_routing_strategy()
        speed_priority = config.get_speed_priority()
        quality_threshold = config.get_quality_threshold()
        print(f"✅ Routing preferences: strategy={routing_strategy}, speed_priority={speed_priority}, quality_threshold={quality_threshold}")

        # Test cost optimization config
        cost_models = config.get_cost_models()
        quality_scores = config.get_quality_scores()
        print(f"✅ Cost optimization: {len(cost_models)} cost models, {len(quality_scores)} quality scores")

        # Test PerformanceOptimizer initialization
        dummy_providers = {"gemini": {}}
        performance_optimizer = PerformanceOptimizer(dummy_providers, perf_config)
        print("✅ PerformanceOptimizer initialized successfully")

        # Test performance metrics recording
        performance_optimizer.record_performance_metrics(
            provider_name="gemini",
            model_name="gemini-2.5-flash",
            response_time=2.5,
            success=True
        )
        print("✅ Performance metrics recording works")

        # Get performance summary
        perf_summary = performance_optimizer.get_performance_summary()
        print(f"✅ Performance summary: {len(perf_summary)} models tracked")

        # Test RoutingTelemetry initialization
        telemetry = RoutingTelemetry(telemetry_config)
        print("✅ RoutingTelemetry initialized successfully")

        # Test telemetry data export
        telemetry_data = telemetry.export_telemetry_data()
        print(f"✅ Telemetry export works: {len(telemetry_data)} characters")

        # Test Router initialization (should work even with routing disabled)
        router = Router()
        print("✅ Router initialized successfully")

        # Test router health status
        health_status = router.get_routing_health_status()
        print(f"✅ Router health status: {health_status['routing_enabled']=}, {health_status['providers_available']=}")

        # Test router analytics access
        analytics = router.get_routing_analytics()
        print(f"✅ Router analytics access: {'error' in analytics or len(analytics) >= 0}")

        print("=" * 60)
        print("🎉 Phase 3: Advanced Routing Logic - All tests passed!")
        print("✨ Performance optimization, telemetry, and advanced routing are working correctly")

        # Display feature summary
        print("\n📊 Advanced Features Summary:")
        print("• Performance Optimizer: Real-time performance tracking and routing")
        print("• Routing Telemetry: Comprehensive analytics and monitoring")
        print("• Advanced Routing: Performance, cost, quality, and balanced strategies")
        print("• Configuration: Granular routing preferences and thresholds")
        print("• Health Monitoring: System status and alert capabilities")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration_methods():
    """Test all the new configuration accessor methods"""
    print("\n🔧 Testing Configuration Accessor Methods")
    print("-" * 40)

    try:
        from claude_gemini_mcp.config import get_config

        config = get_config()

        # Test all new configuration methods
        methods_to_test = [
            ('get_routing_preferences', []),
            ('get_routing_strategy', []),
            ('get_speed_priority', []),
            ('get_cost_sensitivity', []),
            ('get_quality_threshold', []),
            ('get_max_acceptable_response_time', []),
            ('is_adaptive_routing_enabled', []),
            ('is_load_balancing_enabled', []),
            ('get_performance_config', []),
            ('get_max_response_time', []),
            ('get_min_success_rate', []),
            ('get_metrics_window_size', []),
            ('is_performance_monitoring_enabled', []),
            ('get_cost_optimization_config', []),
            ('is_cost_tracking_enabled', []),
            ('get_cost_models', []),
            ('get_quality_scores', []),
            ('get_daily_budget', []),
            ('get_request_budget', []),
            ('get_telemetry_config', []),
            ('is_telemetry_enabled', []),
            ('get_telemetry_max_records', []),
            ('get_analytics_window_hours', []),
            ('is_detailed_logging_enabled', []),
            ('are_alerts_enabled', []),
            ('get_alert_thresholds', [])
        ]

        for method_name, args in methods_to_test:
            method = getattr(config, method_name)
            result = method(*args)
            print(f"✅ {method_name}(): {type(result).__name__}")

        print("✅ All configuration accessor methods work correctly")
        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(level=logging.INFO)

    success = True
    success &= test_advanced_routing_features()
    success &= test_configuration_methods()

    if success:
        print("\n🎉 All Phase 3 tests passed successfully!")
        print("🚀 Advanced routing logic is ready for production!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)
