export type NullStrategy = "mean" | "forwardFill" | "drop" | "none";

export interface CleanDataOptions {
  nullStrategy?: NullStrategy;
  zScoreThreshold?: number;
  minRowsForOutlierScan?: number;
  standardizeStringCase?: boolean;
}

type RawRow = Record<string, unknown>;
type ColumnKind = "number" | "date" | "boolean" | "string";

const NULL_TOKENS = new Set(["", "null", "nil", "none", "na", "n/a", "nan", "-", "--"]);

const DEFAULT_OPTIONS: Required<CleanDataOptions> = {
  nullStrategy: "mean",
  zScoreThreshold: 3,
  minRowsForOutlierScan: 8,
  standardizeStringCase: true,
};

export function cleanData<T extends RawRow>(rows: T[], options: CleanDataOptions = {}): RawRow[] {
  const settings = { ...DEFAULT_OPTIONS, ...options };
  if (!Array.isArray(rows) || rows.length === 0) return [];

  const normalizedRows = rows
    .map((row) => normalizeRow(row, settings))
    .filter((row) => Object.values(row).some((value) => value !== null));

  const dedupedRows = dedupeRows(normalizedRows);
  if (dedupedRows.length === 0) return [];

  const columns = collectColumns(dedupedRows);
  const columnKinds = inferColumnKinds(dedupedRows, columns);
  const coercedRows = dedupedRows.map((row) => coerceRow(row, columns, columnKinds));
  const nullHandledRows = handleNulls(coercedRows, columns, columnKinds, settings.nullStrategy);

  return dropZScoreOutliers(
    nullHandledRows,
    columns.filter((column) => columnKinds[column] === "number"),
    settings.zScoreThreshold,
    settings.minRowsForOutlierScan,
  );
}

function normalizeRow(row: RawRow, options: Required<CleanDataOptions>): RawRow {
  return Object.entries(row).reduce<RawRow>((acc, [rawKey, rawValue]) => {
    const key = normalizeColumnName(rawKey);
    if (!key) return acc;

    const value = normalizeScalar(rawValue, options.standardizeStringCase);
    if (acc[key] === undefined || acc[key] === null) {
      acc[key] = value;
      return acc;
    }

    const nextKey = uniqueColumnName(acc, key);
    acc[nextKey] = value;
    return acc;
  }, {});
}

function normalizeColumnName(key: string): string {
  const cleaned = key.trim().replace(/\s+/g, " ");
  if (!cleaned) return "";

  const camel = cleaned
    .replace(/[^a-zA-Z0-9]+(.)/g, (_, character: string) => character.toUpperCase())
    .replace(/^[A-Z]/, (character) => character.toLowerCase());

  return camel || cleaned;
}

function uniqueColumnName(row: RawRow, baseKey: string): string {
  let index = 2;
  let key = `${baseKey}${index}`;

  while (Object.prototype.hasOwnProperty.call(row, key)) {
    index += 1;
    key = `${baseKey}${index}`;
  }

  return key;
}

function normalizeScalar(value: unknown, standardizeStringCase: boolean): unknown {
  if (value === undefined || value === null) return null;

  if (typeof value === "number") {
    return Number.isFinite(value) ? value : null;
  }

  if (typeof value === "string") {
    const trimmed = value.trim().replace(/\s+/g, " ");
    if (NULL_TOKENS.has(trimmed.toLowerCase())) return null;
    return standardizeStringCase ? standardizeCase(trimmed) : trimmed;
  }

  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : value.toISOString();
  }

  return value;
}

function standardizeCase(value: string): string {
  if (looksLikeEmailUrlOrId(value)) return value;
  if (!/[a-zA-Z]/.test(value)) return value;

  return value
    .toLowerCase()
    .replace(/\b[a-z]/g, (character) => character.toUpperCase());
}

function looksLikeEmailUrlOrId(value: string): boolean {
  const isCodeLike = /^[A-Za-z0-9_-]{4,}$/.test(value) && (/[\d_-]/.test(value) || value === value.toUpperCase());

  return (
    value.includes("@") ||
    /^https?:\/\//i.test(value) ||
    isCodeLike ||
    /[a-z]+[A-Z]+/.test(value)
  );
}

function dedupeRows(rows: RawRow[]): RawRow[] {
  const seen = new Set<string>();
  const deduped: RawRow[] = [];

  for (const row of rows) {
    const signature = stableStringify(row);
    if (seen.has(signature)) continue;
    seen.add(signature);
    deduped.push(row);
  }

  return deduped;
}

function stableStringify(row: RawRow): string {
  return JSON.stringify(
    Object.keys(row)
      .sort()
      .reduce<RawRow>((acc, key) => {
        acc[key] = row[key];
        return acc;
      }, {}),
  );
}

function collectColumns(rows: RawRow[]): string[] {
  const columns = new Set<string>();
  rows.forEach((row) => Object.keys(row).forEach((column) => columns.add(column)));
  return Array.from(columns);
}

function inferColumnKinds(rows: RawRow[], columns: string[]): Record<string, ColumnKind> {
  return columns.reduce<Record<string, ColumnKind>>((acc, column) => {
    const values = rows.map((row) => row[column]).filter((value) => value !== null && value !== undefined);
    const sampleSize = values.length;

    if (sampleSize === 0) {
      acc[column] = "string";
      return acc;
    }

    const numericRatio = values.filter((value) => parseNumber(value) !== null).length / sampleSize;
    const dateRatio = values.filter((value) => parseDate(value) !== null).length / sampleSize;
    const booleanRatio = values.filter((value) => parseBoolean(value) !== null).length / sampleSize;

    if (numericRatio >= 0.8) acc[column] = "number";
    else if (dateRatio >= 0.75) acc[column] = "date";
    else if (booleanRatio >= 0.9) acc[column] = "boolean";
    else acc[column] = "string";

    return acc;
  }, {});
}

function coerceRow(row: RawRow, columns: string[], columnKinds: Record<string, ColumnKind>): RawRow {
  return columns.reduce<RawRow>((acc, column) => {
    const value = row[column] ?? null;

    if (value === null) {
      acc[column] = null;
      return acc;
    }

    if (columnKinds[column] === "number") acc[column] = parseNumber(value);
    else if (columnKinds[column] === "date") acc[column] = parseDate(value);
    else if (columnKinds[column] === "boolean") acc[column] = parseBoolean(value);
    else acc[column] = value;

    return acc;
  }, {});
}

function parseNumber(value: unknown): number | null {
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  if (typeof value !== "string") return null;

  const percent = value.trim().endsWith("%");
  const cleaned = value.replace(/[$,%\s]/g, "");
  if (!cleaned || cleaned === "." || cleaned === "-") return null;

  const parsed = Number(cleaned);
  if (!Number.isFinite(parsed)) return null;
  return percent ? parsed / 100 : parsed;
}

function parseDate(value: unknown): string | null {
  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : value.toISOString();
  }

  if (typeof value !== "string") return null;
  if (!looksDateLike(value)) return null;

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return null;

  const hasTime = /(\d{1,2}:\d{2})|T/i.test(value);
  return hasTime ? parsed.toISOString() : parsed.toISOString().slice(0, 10);
}

function looksDateLike(value: string): boolean {
  const trimmed = value.trim();
  return (
    /^\d{4}[-/]\d{1,2}[-/]\d{1,2}/.test(trimmed) ||
    /^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}/.test(trimmed) ||
    /^[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}/.test(trimmed)
  );
}

function parseBoolean(value: unknown): boolean | null {
  if (typeof value === "boolean") return value;
  if (typeof value !== "string") return null;

  const normalized = value.trim().toLowerCase();
  if (["true", "yes", "y", "1"].includes(normalized)) return true;
  if (["false", "no", "n", "0"].includes(normalized)) return false;

  return null;
}

function handleNulls(
  rows: RawRow[],
  columns: string[],
  columnKinds: Record<string, ColumnKind>,
  strategy: NullStrategy,
): RawRow[] {
  if (strategy === "none") return rows;

  if (strategy === "drop") {
    return rows.filter((row) => columns.every((column) => row[column] !== null && row[column] !== undefined));
  }

  if (strategy === "forwardFill") return forwardFillRows(rows, columns);

  const means = calculateMeans(rows, columns.filter((column) => columnKinds[column] === "number"));

  return forwardFillRows(rows, columns).map((row) => {
    const nextRow = { ...row };
    for (const column of columns) {
      if (nextRow[column] !== null && nextRow[column] !== undefined) continue;
      nextRow[column] = columnKinds[column] === "number" ? means[column] ?? 0 : null;
    }
    return nextRow;
  });
}

function forwardFillRows(rows: RawRow[], columns: string[]): RawRow[] {
  const lastSeen: RawRow = {};

  return rows.map((row) => {
    const nextRow = { ...row };

    for (const column of columns) {
      if (nextRow[column] === null || nextRow[column] === undefined) {
        nextRow[column] = lastSeen[column] ?? null;
      } else {
        lastSeen[column] = nextRow[column];
      }
    }

    return nextRow;
  });
}

function calculateMeans(rows: RawRow[], numericColumns: string[]): Record<string, number> {
  return numericColumns.reduce<Record<string, number>>((acc, column) => {
    const values = rows
      .map((row) => row[column])
      .filter((value): value is number => typeof value === "number" && Number.isFinite(value));

    if (values.length > 0) {
      acc[column] = values.reduce((sum, value) => sum + value, 0) / values.length;
    }

    return acc;
  }, {});
}

function dropZScoreOutliers(
  rows: RawRow[],
  numericColumns: string[],
  threshold: number,
  minRowsForOutlierScan: number,
): RawRow[] {
  if (rows.length < minRowsForOutlierScan || numericColumns.length === 0) return rows;

  const stats = numericColumns.reduce<Record<string, { mean: number; standardDeviation: number }>>((acc, column) => {
    const values = rows
      .map((row) => row[column])
      .filter((value): value is number => typeof value === "number" && Number.isFinite(value));

    if (values.length < minRowsForOutlierScan) return acc;

    const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
    const variance = values.reduce((sum, value) => sum + (value - mean) ** 2, 0) / values.length;
    const standardDeviation = Math.sqrt(variance);

    if (standardDeviation > 0) acc[column] = { mean, standardDeviation };
    return acc;
  }, {});

  return rows.filter((row) =>
    Object.entries(stats).every(([column, { mean, standardDeviation }]) => {
      const value = row[column];
      if (typeof value !== "number" || !Number.isFinite(value)) return true;
      return Math.abs((value - mean) / standardDeviation) <= threshold;
    }),
  );
}
