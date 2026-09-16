from pathlib import Path

from eak_kernel.conformance import PaperConformanceHarness

ROOT = Path(__file__).parents[1]


def test_medical_aec_legal_compile_without_kernel_domain_switches():
    results = PaperConformanceHarness(ROOT).run_all()
    assert [item["domain"] for item in results] == ["medical", "aec", "legal"]
    assert all(item["pass"] for item in results), results


def test_decoy_provider_is_rejected_and_never_selected():
    medical = PaperConformanceHarness(ROOT).run_domain("medical")
    assert medical["bindings"]["classify"]["id"] == "provider.xray.local"
    resolved_events = [event for event in medical["events"] if event == "ProviderResolved"]
    assert len(resolved_events) == 2
