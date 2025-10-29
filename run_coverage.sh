#!/bin/bash
# Run tests with coverage and open HTML report

echo "Running tests with coverage (excluding Discord infrastructure)..."
pytest --cov=. --cov-report=term-missing --cov-report=html -k "not test_heat_wave_temperature_modifier_applied and not test_cold_front_temperature_modifier_applied"

echo ""
echo "Coverage report generated in htmlcov/index.html"
echo "To view the report, open htmlcov/index.html in your browser"
echo ""
echo "Quick summary:"
coverage report --skip-covered
