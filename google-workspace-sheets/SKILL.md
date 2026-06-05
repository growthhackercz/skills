---
name: Google Workspace Sheets
description: Use Google Sheets through the gog-safe wrapper for reading, updating, appending, formatting, creating, and exporting spreadsheets. Requires the Google Workspace sheets service to be authorized.
category: integrations
status: ready
version: "1.1"
publishedAt: "2026-05-19"
---

# Skill: Google Workspace Sheets

Use this skill for spreadsheet work through `gog-safe`.

## Required Authorization

- Control Center service: `sheets`.
- Exports and file copies may also require Drive access.
- If commands fail with insufficient scopes, ask the operator to reconnect
  Google Workspace with Sheets enabled.
- Embedded charts use the Sheets API through `gog-safe sheets add-chart`;
  they do not require Apps Script.

## Workflow

1. Check account state with `gog-safe status --json`.
2. When creating a new spreadsheet for a known Drive folder, use
   `gog-safe sheets create ... --parent <folderId>` instead of creating first
   and moving it later.
3. For generated data, write the whole table in one update using
   `--values-json` and `--input USER_ENTERED`. This lets formulas such as
   `=A2^2` evaluate correctly and avoids the positional-argument pitfall where
   only `A1` is updated.
4. Read metadata first when sheet names or ranges are unclear.
5. Confirm target range and values before updates, appends, clears, formatting,
   tab changes, or chart changes.
6. After writing data, verify with `gog-safe sheets get ... --json --no-input`.

## Fast Path: Add Chart To Existing Sheet

When the user asks only to add a chart to an existing spreadsheet and the data
range is already known, do not explore Apps Script, raw Google REST, Python, or
the legacy `gog` skill. Use `gog-safe sheets add-chart` directly:

```bash
gog-safe sheets add-chart <spreadsheetId> --sheet "<tabName>" --x-range 'A2:A7' --y-range 'B2:B7' --title 'y=x^2' --type LINE --position 'E2' --x-title 'x' --y-title 'y=x^2' --json --no-input
```

For the existing demo sheet with columns `A=x` and `B=y=x^2`, the command shape
is:

```bash
gog-safe sheets add-chart 1RJmWELJs10LhTKWrZpiDLOAT1pm7eRejMjgRj_SOTvs --sheet "List 1" --x-range 'A2:A7' --y-range 'B2:B7' --title 'y=x^2' --type LINE --position 'E2' --x-title 'x' --y-title 'y=x^2' --json --no-input
```

If `gog-safe sheets add-chart --help` does not show this helper, the OpenClaw
runtime image is stale. Stop and report that the runtime needs the current
Control Center/OpenClaw image; do not attempt Apps Script or direct token/API
workarounds.

## Commands

```bash
gog-safe sheets create "Report" --sheets "Data" --parent <folderId> --json --no-input
gog-safe sheets metadata <spreadsheetId> --json --no-input
gog-safe sheets get <spreadsheetId> 'Sheet1!A1:D20' --json --no-input
gog-safe sheets named-ranges <spreadsheetId> --json --no-input
gog-safe sheets export <spreadsheetId> --format xlsx --out ./sheet.xlsx --json --no-input
```

Mutations after confirmation:

```bash
gog-safe sheets update <spreadsheetId> 'Sheet1!A1:C3' --input USER_ENTERED --values-json '[["x","y=x^2"],[0,"=A2^2"],[1,"=A3^2"]]' --json --no-input
gog-safe sheets append <spreadsheetId> 'Sheet1!A:C' 'new|row|data' --json --no-input
gog-safe sheets clear <spreadsheetId> 'Sheet1!A1:B10' --json --no-input
gog-safe sheets add-tab <spreadsheetId> "New Tab" --json --no-input
gog-safe sheets format <spreadsheetId> 'Sheet1!A1:B2' --format-json '{"textFormat":{"bold":true}}' --format-fields 'userEnteredFormat.textFormat.bold' --json --no-input
gog-safe sheets freeze <spreadsheetId> --sheet "Sheet1" --rows 1 --json --no-input
gog-safe sheets resize-columns <spreadsheetId> 'Sheet1!A:B' --width 120 --json --no-input
gog-safe sheets add-chart <spreadsheetId> --sheet "Sheet1" --x-range 'A2:A7' --y-range 'B2:B7' --title 'y=x^2' --type LINE --position 'D2' --x-title 'x' --y-title 'y' --json --no-input
```

## Create Data And Chart From Scratch

For a task like "create a sheet in folder pokusy, invent data, formulas, and a
chart", use this order:

```bash
# 1. Find or create the folder with the Drive skill, then create the sheet in it.
gog-safe sheets create "pokusy - kvadratická funkce" --sheets "Data" --parent <pokusyFolderId> --json --no-input

# 2. Write all data and formulas in one request.
gog-safe sheets update <spreadsheetId> 'Data!A1:B7' --input USER_ENTERED --values-json '[["x","y=x^2"],[0,"=A2^2"],[1,"=A3^2"],[2,"=A4^2"],[3,"=A5^2"],[4,"=A6^2"],[5,"=A7^2"]]' --json --no-input

# 3. Make the table readable.
gog-safe sheets format <spreadsheetId> 'Data!A1:B1' --format-json '{"textFormat":{"bold":true},"backgroundColor":{"red":0.9,"green":0.95,"blue":1}}' --format-fields 'userEnteredFormat.textFormat.bold,userEnteredFormat.backgroundColor' --json --no-input
gog-safe sheets freeze <spreadsheetId> --sheet "Data" --rows 1 --json --no-input
gog-safe sheets resize-columns <spreadsheetId> 'Data!A:B' --width 120 --json --no-input

# 4. Add the chart directly through the Sheets API helper.
gog-safe sheets add-chart <spreadsheetId> --sheet "Data" --x-range 'A2:A7' --y-range 'B2:B7' --title 'y=x^2' --type LINE --position 'D2' --x-title 'x' --y-title 'y' --json --no-input

# 5. Verify values before reporting completion.
gog-safe sheets get <spreadsheetId> 'Data!A1:B7' --json --no-input
```

## Guardrails

- Do not overwrite broad ranges such as whole columns without confirmation.
- Preserve formulas and validation rules unless the user asks to replace them.
- For generated tables, show a preview of headers and first rows before writing.
- Do not read or use `skills/gog/SKILL.md` or `/app/skills/gog/SKILL.md`.
  Google Workspace instructions come from `google-workspace-*` skills.
- Do not use Apps Script for charts unless the user explicitly asks for Apps
  Script automation. Use `gog-safe sheets add-chart` first.
- If chart creation fails with insufficient scope, report that the Sheets
  service must be reconnected; do not switch to Apps Script as a workaround.
