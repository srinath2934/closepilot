"""Unit tests for deterministic opportunity scoring service."""
import pytest
from app.graph.nodes.prioritize import calculate_opportunity_score


def test_high_value_contract_sent_scoring():
    deal = {
        "id": "deal_1",
        "name": "Enterprise Deal",
        "amount": 80000.0,
        "stage": "Contract Sent",
        "days_inactive": 5,
        "has_future_task": False
    }
    score, reasons = calculate_opportunity_score(deal)
    # Stage (35) + High Value (30) + Inactivity (25) = 90
    assert score == 90.0
    assert len(reasons) == 3
    assert any("Tier-1 enterprise value" in r for r in reasons)


def test_recent_contact_penalty():
    deal = {
        "id": "deal_2",
        "name": "Just Contacted Deal",
        "amount": 25000.0,
        "stage": "Qualified to Buy",
        "days_inactive": 1,
        "has_future_task": False
    }
    score, reasons = calculate_opportunity_score(deal)
    # Stage (15) + Value (20) - Recent Contact (50) = -15
    assert score == -15.0
    assert any("Contacted within the last 24-48 hours" in r for r in reasons)


def test_future_task_penalty():
    deal = {
        "id": "deal_3",
        "name": "Already Handled Deal",
        "amount": 50000.0,
        "stage": "Decision Maker Bought-In",
        "days_inactive": 4,
        "has_future_task": True
    }
    score, reasons = calculate_opportunity_score(deal)
    # Stage (30) + Value (30) + Inactivity (20) - Future Task (40) = 40
    assert score == 40.0
    assert any("Existing follow-up task already scheduled" in r for r in reasons)
