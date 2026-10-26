export interface ScheduledEmailCheckpoint {
  stepId: string;
  emailMessageId: string;
  scheduledTimestamp: number;
}

export interface ParsedScheduledState {
  processing: boolean;
  processingStartedAt: number | null;
  ids: string[];
  entries: ScheduledEmailCheckpoint[];
}

function unique(values: string[]): string[] {
  return [...new Set(values)];
}

/** Parse the final ID array or an append-only in-progress checkpoint. */
export function parseScheduledField(raw: string): ParsedScheduledState {
  if (!raw) {
    return { processing: false, processingStartedAt: null, ids: [], entries: [] };
  }

  try {
    const parsed = JSON.parse(raw) as unknown;
    if (Array.isArray(parsed)) {
      return {
        processing: false,
        processingStartedAt: null,
        ids: unique(
          parsed.filter((value): value is string => typeof value === "string" && value.length > 0)
        ),
        entries: [],
      };
    }

    if (
      parsed &&
      typeof parsed === "object" &&
      (parsed as Record<string, unknown>).state === "processing"
    ) {
      const state = parsed as Record<string, unknown>;
      const startedAt = Number(state.startedAt ?? 0);
      const entries = Array.isArray(state.entries)
        ? state.entries.filter((entry): entry is ScheduledEmailCheckpoint => {
            if (!entry || typeof entry !== "object") return false;
            const value = entry as Record<string, unknown>;
            return (
              typeof value.stepId === "string" &&
              value.stepId.length > 0 &&
              typeof value.emailMessageId === "string" &&
              value.emailMessageId.length > 0 &&
              typeof value.scheduledTimestamp === "number" &&
              Number.isFinite(value.scheduledTimestamp)
            );
          })
        : [];
      const ids = Array.isArray(state.ids)
        ? state.ids.filter(
            (value): value is string => typeof value === "string" && value.length > 0
          )
        : [];

      return {
        processing: true,
        processingStartedAt:
          Number.isFinite(startedAt) && startedAt > 0 ? startedAt : null,
        ids: unique([...ids, ...entries.map((entry) => entry.emailMessageId)]),
        entries,
      };
    }
  } catch {
    // Invalid state is treated as empty and can be repaired by the next run.
  }

  return { processing: false, processingStartedAt: null, ids: [], entries: [] };
}
