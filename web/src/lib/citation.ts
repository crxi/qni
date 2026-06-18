/**
 * Shared citation helpers used by SourceNote (inline) and
 * ReferencesList (bottom-of-page bibliography). Keeping the marker
 * formatting in one place ensures the inline label and the
 * bibliography label are always identical — so a reader can scan
 * a "Kumar et al. 2025" superscript and find the same string in
 * the bibliography below.
 */

export interface SourceEntry {
  id: string;
  title: string;
  authors?: string[];
  publisher?: string;
  year: number | string;
  url?: string;
  doi?: string;
  type: string;
  /** Explicit citation marker — for standards (RFC 9340, ITU-T G.694.2). */
  marker?: string;
}

export function surname(name: string): string {
  const parts = name.trim().split(/\s+/);
  return parts[parts.length - 1];
}

/**
 * Short marker used in inline citations and as the lookup label
 * in the bibliography. Priority:
 *   1. Explicit `marker` field — used for standards.
 *   2. Author surname(s) — "Surname" or "Surname et al." for ≥2.
 *   3. Publisher / title fallback.
 *
 * The year is NOT included here; callers add it where appropriate
 * (the inline citation appends it as a separate span; the
 * bibliography label appends it via `bibliographyLabel`).
 */
export function markerFor(entry: SourceEntry): string {
  if (entry.marker) return entry.marker;
  if (entry.authors && entry.authors.length > 0) {
    if (entry.authors.length >= 2) return `${surname(entry.authors[0])} et al.`;
    return surname(entry.authors[0]);
  }
  return entry.publisher ?? entry.title;
}

/**
 * Bibliography label — the bracketed text that prefixes each entry
 * so a reader scanning from an inline citation can find the entry.
 * Standards (RFC 9340, ITU-T G.694.2) self-identify by their
 * canonical number, so no year is appended; everything else gets
 * the academic "Surname Year" form.
 */
export function bibliographyLabel(entry: SourceEntry): string {
  const m = markerFor(entry);
  if (entry.marker) return m;
  return `${m} ${entry.year}`;
}
