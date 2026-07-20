from __future__ import annotations
from nodebench.speedtest import CloudflareSpeedTest

def run_demo():
    print("\n  NodeBench Demo\n")
    tester = CloudflareSpeedTest()
    trace = tester.fetch_trace()
    if trace.country:
        print(f"  Exit: {trace.country}/{trace.colo} ({trace.ip})")
    else:
        print("  Exit: (no trace)")
    print(f"  Test Download (10 MB)...")
    dl = tester.run_download(10_000_000)
    print(f"    Download: {dl.mbps:.1f} Mbps")
    print(f"  Test Upload (5 MB)...")
    ul = tester.run_upload(5_000_000)
    print(f"    Upload:   {ul.mbps:.1f} Mbps")
    print("\n  Demo done.\n")
