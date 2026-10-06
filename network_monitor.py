import json
import subprocess
import time
from datetime import datetime
from pathlib import Path


# Common service ports
COMMON_PORTS = {22, 53, 80, 443}

# Report locations
REPORT_DIR = Path("reports")
LATEST_REPORT = REPORT_DIR / "latest_report.json"
HISTORY_REPORT = REPORT_DIR / "monitoring_history.json"


def analyze_listening_service(line):
    """Analyze a listening TCP service and generate a finding if needed."""
    parts = line.split()

    if len(parts) < 5:
        return None

    local_address = parts[3]

    try:
        port = int(local_address.rsplit(":", 1)[-1])
    except ValueError:
        return None

    if port not in COMMON_PORTS:
        if local_address.startswith("127.0.0.1:"):
            severity = "LOW"
            reason = "Non-standard listening port detected on localhost."
        else:
            severity = "MEDIUM"
            reason = "Non-standard listening port detected."

        return {
            "type": "Non-standard Listening Port",
            "port": port,
            "severity": severity,
            "reason": reason
        }

    return None


def collect_connections(cycle):
    """Collect TCP connection information using the ss utility."""
    result = subprocess.run(
        ["ss", "-tan"],
        capture_output=True,
        text=True,
        check=True
    )

    listening_services = []
    established_connections = []
    findings = []

    for line in result.stdout.splitlines():
        if line.startswith("State") or not line.strip():
            continue

        parts = line.split()

        if len(parts) < 4:
            continue

        state = parts[0]

        if state == "LISTEN":
            listening_services.append(line)

            finding = analyze_listening_service(line)

            if finding:
                findings.append(finding)

        elif state == "ESTAB":
            established_connections.append(line)

    severity = "INFO"

    if any(item["severity"] == "MEDIUM" for item in findings):
        severity = "MEDIUM"
    elif any(item["severity"] == "LOW" for item in findings):
        severity = "LOW"

    return {
        "cycle": cycle,
        "timestamp": datetime.now().isoformat(),
        "listening_services": listening_services,
        "established_connections": established_connections,
        "findings": findings,
        "severity": severity
    }


def save_reports(report, history):
    """Save the latest report and monitoring history as JSON."""
    REPORT_DIR.mkdir(exist_ok=True)

    with open(LATEST_REPORT, "w") as file:
        json.dump(report, file, indent=4)

    with open(HISTORY_REPORT, "w") as file:
        json.dump(history, file, indent=4)


def main():
    """Run five monitoring cycles with a ten-second interval."""
    history = []

    print("=" * 60)
    print("Network Monitoring & Alerting System")
    print("=" * 60)

    for cycle in range(1, 6):
        print(f"\n[+] Monitoring Cycle {cycle}/5")

        report = collect_connections(cycle)
        history.append(report)

        save_reports(report, history)

        print(f"    Listening services : {len(report['listening_services'])}")
        print(f"    Established connections : {len(report['established_connections'])}")
        print(f"    Findings : {len(report['findings'])}")
        print(f"    Severity : {report['severity']}")

        if cycle < 5:
            time.sleep(10)

    print("\n[+] Monitoring completed.")
    print(f"[+] Latest report saved to: {LATEST_REPORT}")
    print(f"[+] Monitoring history saved to: {HISTORY_REPORT}")


if __name__ == "__main__":
    main()
