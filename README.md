# Knihovna skillů

Samostatné skilly jsou ve složkách s `SKILL.md`; podle typu obsahují reference, skripty a testy.

- [Dokumentace](docs/README.md)
- [Audit původního CliqSales AI a rozdíly knihoven](docs/audits/cliqsales-ai-architecture.md)

Zpřístupnění skillu agentovi není automatická instalace závislostí nebo připojení externích služeb. Původní CliqSales skilly mohou vyžadovat OpenClaw / Control Center, sdílené helpery, nástroje a credentials. Samotný `SKILL.md` nepotvrzuje end-to-end funkčnost.

Do repozitáře nepatří API klíče, cookies, OAuth tokeny, živé konfigurace ani soukromé agentní paměti. Audit publikuje technické závěry a strukturální důkazy, ne obsah soukromé zálohy.
