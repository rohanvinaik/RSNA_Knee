# Hosted SonarCloud analysis

The public [rohanvinaik_RSNA_Knee project](https://sonarcloud.io/project/overview?id=rohanvinaik_RSNA_Knee)
belongs to the existing `rohanvinaik` organization and is bound to the public GitHub repository.
Rohan supplied `.github/workflows/build.yml`: the macOS GitHub Actions job uses the pinned checkout,
cache and Sonar scanner actions, with the encrypted `SONAR_TOKEN` repository secret. No token value
belongs in source or documentation.

The scanner reads `sonar-project.properties`; its command-line arguments override the local project
key with `rohanvinaik_RSNA_Knee` and add the Cloud organization. This preserves the production package
and runner scope, separates tests, and excludes both archived builds and data. No active production
code is omitted to satisfy a subscription allowance.

## Setup and verification

1. Under **Administration → Permissions**, verify that project visibility is Public, matching GitHub.
2. Under **Administration → Analysis method**, keep **Automatic analysis off**. It conflicts with
   the requested CI-based Cloud analysis.
3. In GitHub **Settings → Secrets and variables → Actions**, configure the `SONAR_TOKEN` repository
   secret with a SonarCloud token authorized to analyze the project. The local SonarQube token is a
   different credential and cannot substitute for it.
4. Push to `main` or update a pull request. Inspect the `SonarQube` workflow's `Build and analyze` job,
   then the hosted background-task result and dashboard. A connected project is not a completed scan.

The existing `gate` and `codspeed` workflows remain active. The declared gate still runs the pinned
SonarQube server/scanner with actual test coverage and the accepted bare-correctness blocking policy.
The supplied Cloud job scans without building or generating coverage; the gate's separate-job
`coverage.xml` is not automatically available to it. Do not claim hosted coverage was imported.
Cloud quality-gate conditions and subscription errors remain distinct from the declared local gate.

The active packet links source-pinned setup and execution evidence. An initial automatic scan failed
under private-code quota before Rohan made the project public; it is historical, superseded evidence.
The unused `.sonarcloud.properties` candidate was withdrawn when he selected the CI workflow.

References: [CI and automatic-analysis conflicts](https://docs.sonarsource.com/sonarqube-cloud/analyzing-source-code/automatic-analysis),
[Cloud analysis authentication](https://docs.sonarsource.com/sonarqube-cloud/appendices/troubleshooting).
