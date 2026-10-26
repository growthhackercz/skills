const LARGE_TEXT_RENDERS = new Set(["text", "steps", "openloop", "cards"]);
const LARGE_TEXT_FIELDS = new Set([
  "predpis_config",
  "souhrn_ted",
  "souhrn_chci",
  "pointa",
  "nalehavost",
  "obraz_potom",
]);

function normalizedType(value) {
  return String(value ?? "").trim().toUpperCase();
}

export function buildFieldPlan({ tagPrefix, personaFields, magnetBlocks = [] }) {
  const renderByField = new Map();
  for (const block of magnetBlocks) {
    if (block?.persona_field && block?.render) {
      renderByField.set(block.persona_field, block.render);
    }
  }

  function personaType(fieldName) {
    const render = renderByField.get(fieldName);
    if (
      LARGE_TEXT_FIELDS.has(fieldName) ||
      fieldName.startsWith("magnet_") ||
      LARGE_TEXT_RENDERS.has(render)
    ) {
      return "LARGE_TEXT";
    }
    return "TEXT";
  }

  const persona = personaFields.map((fieldName) => ({
    key: fieldName,
    name: `${tagPrefix} - ${fieldName}`,
    dataType: personaType(fieldName),
  }));

  return {
    persona,
    temperature: {
      name: `${tagPrefix} - Temperature`,
      dataType: "TEXT",
    },
    scheduledIds: {
      name: `${tagPrefix} - Scheduled IDs`,
      dataType: "LARGE_TEXT",
    },
    sequenceEnd: {
      name: `${tagPrefix} - Sequence End`,
      dataType: "TEXT",
    },
  };
}

export function findFieldTypeMismatches(existingFields, plannedFields) {
  const existingByName = new Map(
    existingFields
      .filter((field) => field?.name)
      .map((field) => [String(field.name).trim().toLowerCase(), field])
  );
  const mismatches = [];

  for (const planned of plannedFields) {
    const existing = existingByName.get(planned.name.trim().toLowerCase());
    if (!existing) continue;
    const actual = normalizedType(existing.dataType);
    const expected = normalizedType(planned.dataType);
    if (actual !== expected) {
      mismatches.push({
        name: planned.name,
        expected,
        actual: actual || "NEZNÁMÝ",
      });
    }
  }
  return mismatches;
}
