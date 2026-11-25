"""Create a keyless Sheets reader and grant narrowly scoped impersonation access."""

import argparse
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--region", default="europe-west1")
    parser.add_argument("--service", default="janus-api")
    parser.add_argument("--reader-name", default="minerva-sheets-reader")
    parser.add_argument("--developer-email", help="Optional local developer allowed to impersonate the reader")
    args = parser.parse_args()
    executable = shutil.which("gcloud.cmd") or shutil.which("gcloud")
    if not executable:
        parser.error("Install the Google Cloud CLI and run gcloud auth login first.")

    def run(*parts):
        result = subprocess.run([executable, *parts, f"--project={args.project}", "--quiet"],
                                text=True, capture_output=True, check=False)
        if result.returncode:
            raise SystemExit(result.stderr.strip() or "Google Cloud setup failed.")
        return result.stdout.strip()

    # Discover the existing runtime rather than granting access to a guessed identity.
    runtime = run("run", "services", "describe", args.service, f"--region={args.region}",
                  "--format=value(spec.template.spec.serviceAccountName)")
    if not runtime.endswith(".gserviceaccount.com"):
        parser.error("Could not determine the Janus runtime service account.")
    reader = f"{args.reader_name}@{args.project}.iam.gserviceaccount.com"
    existing = run("iam", "service-accounts", "list", f"--filter=email:{reader}", "--format=value(email)")
    run("services", "enable", "iam.googleapis.com", "iamcredentials.googleapis.com", "sheets.googleapis.com")
    if reader not in existing.splitlines():
        run("iam", "service-accounts", "create", args.reader_name,
            "--display-name=Minerva Sheets reader", "--description=Reads explicitly shared finance workbooks")
    principals = [f"serviceAccount:{runtime}"]
    if args.developer_email:
        principals.append(f"user:{args.developer_email}")
    for principal in principals:
        run("iam", "service-accounts", "add-iam-policy-binding", reader,
            f"--member={principal}", "--role=roles/iam.serviceAccountTokenCreator", "--condition=None")
    print(f"Reader created/configured: {reader}")
    print("Share the finance workbook with this email as Viewer.")
    print(f"Configure Janus with FINANCE_SHEETS_SERVICE_ACCOUNT={reader}")
    print("No keys were created; no Cloud Run deployment was performed.")


if __name__ == "__main__":
    main()
