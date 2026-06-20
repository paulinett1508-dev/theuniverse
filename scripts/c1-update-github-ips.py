#!/usr/bin/env python3
"""C1 — Escudos: restringe porta 9120 aos IPs oficiais do GitHub.

Roda na Polaris (precisa de root para ufw).
Idempotente: limpa todas as regras existentes de 9120 e recria.

Uso:
  python3 scripts/c1-update-github-ips.py
  python3 scripts/c1-update-github-ips.py --dry-run
"""
import json
import re
import subprocess
import sys
import urllib.request

PORT = 9120


def get_github_cidrs() -> list[str]:
    with urllib.request.urlopen("https://api.github.com/meta", timeout=10) as r:
        return json.loads(r.read())["hooks"]


def get_port_rule_numbers(port: int) -> list[int]:
    result = subprocess.run(["ufw", "status", "numbered"],
                            capture_output=True, text=True)
    nums = []
    for line in result.stdout.splitlines():
        if str(port) in line:
            m = re.match(r"\[\s*(\d+)\]", line.strip())
            if m:
                nums.append(int(m.group(1)))
    return sorted(nums, reverse=True)  # reverse: delete from bottom up


def clear_port_rules(port: int, dry: bool) -> int:
    nums = get_port_rule_numbers(port)
    for n in nums:
        print(f"  delete rule #{n}")
        if not dry:
            subprocess.run(["ufw", "--force", "delete", str(n)], check=True)
    return len(nums)


def add_rule(cidr: str, port: int, dry: bool) -> None:
    cmd = ["ufw", "allow", "from", cidr, "to", "any", "port", str(port), "proto", "tcp"]
    print(f"  allow from {cidr}")
    if not dry:
        subprocess.run(cmd, check=True)


def main() -> int:
    dry = "--dry-run" in sys.argv
    if dry:
        print("[DRY-RUN]\n")

    print("Buscando IPs do GitHub...")
    cidrs = get_github_cidrs()
    print(f"  {len(cidrs)} CIDRs: {', '.join(cidrs)}\n")

    print(f"Limpando regras existentes para porta {PORT}...")
    removed = clear_port_rules(PORT, dry)
    print(f"  {removed} regras removidas\n")

    print("Adicionando regras por CIDR do GitHub...")
    for cidr in cidrs:
        add_rule(cidr, PORT, dry)
    print(f"\nAdicionando localhost...")
    add_rule("127.0.0.1", PORT, dry)

    if not dry:
        subprocess.run(["ufw", "reload"], check=True)
        print("\nUFW recarregado.")

    print(f"\n{len(cidrs) + 1} regras ativas para porta {PORT}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
