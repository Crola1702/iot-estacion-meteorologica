export function formatDateTime(value?: string | null): string {
  if (!value) {
    return "";
  }

  const normalized = value.includes("T") ? value : value.replace(" ", "T");
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) {
    return value.replace("T", " ");
  }

  return new Intl.DateTimeFormat("en-CA", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(date).replace(",", "");
}

export function formatShortTime(value?: string | null): string {
  if (!value) {
    return "";
  }

  const formatted = formatDateTime(value);
  const parts = formatted.split(" ");
  return parts[1] ?? formatted;
}

export function formatValue(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "--";
  }

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: Math.abs(value) < 10 ? 2 : 1,
  }).format(value);
}

export function formatUnit(unit: string | null | undefined): string {
  return unit ?? "";
}

export function formatLabelWithUnit(label: string, unit: string | null | undefined): string {
  const cleanUnit = formatUnit(unit);
  return cleanUnit ? `${label} (${cleanUnit})` : label;
}
