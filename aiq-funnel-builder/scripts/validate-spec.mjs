const REQUIRED_PERSONA_FIELDS = [
  "main_headline",
  "magnet_headline",
  "sub_headline",
  "problem1_question",
  "problem1_impact",
  "problem1_source",
  "problem2_question",
  "problem2_impact",
  "problem2_source",
  "problem3_question",
  "problem3_impact",
  "problem3_source",
  "benefit_1_title",
  "benefit_1_description",
  "benefit_2_title",
  "benefit_2_description",
  "benefit_3_title",
  "benefit_3_description",
  "objection_1_title",
  "objection_1_response",
  "objection_2_title",
  "objection_2_response",
  "magnet_rozbor",
  "magnet_dobre",
  "magnet_rizika",
  "magnet_akce",
  "predpis_config",
  "souhrn_ted",
  "souhrn_chci",
  "pointa",
  "nalehavost",
  "obraz_potom",
];

const SUPPORTED_VARIANTS = new Set(["score", "audit", "plan"]);
const SUPPORTED_MIDDLE_RENDERS = new Set(["text", "cards", "steps"]);
const PLACEHOLDER_RE =
  /EXAMPLE_|Vzorov(?:á|ý|é)|\(příklad\)|priklad-firmy\.cz|^\s*\[[^\]]+\]\s*$/i;

function isNonEmptyString(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function collectPlaceholderPaths(value, path = "$", found = []) {
  if (typeof value === "string") {
    if (PLACEHOLDER_RE.test(value)) found.push(path);
    return found;
  }
  if (Array.isArray(value)) {
    value.forEach((item, index) =>
      collectPlaceholderPaths(item, `${path}[${index}]`, found)
    );
    return found;
  }
  if (value && typeof value === "object") {
    for (const [key, item] of Object.entries(value)) {
      collectPlaceholderPaths(item, `${path}.${key}`, found);
    }
  }
  return found;
}

export function validateFunnelSpec(spec, { locationId } = {}) {
  const errors = [];
  if (!spec || typeof spec !== "object" || Array.isArray(spec)) {
    return ["kořen funnel-spec.json musí být objekt"];
  }

  if (spec.spec_version !== "0.5") {
    errors.push("spec_version musí být 0.5");
  }
  if (
    !isNonEmptyString(spec.funnel_slug) ||
    spec.funnel_slug.length > 40 ||
    !/^aiq-[a-z0-9]+(?:-[a-z0-9]+)*$/.test(spec.funnel_slug)
  ) {
    errors.push("funnel_slug musí být ASCII kebab-case aiq-… a mít nejvýše 40 znaků");
  }
  if (!SUPPORTED_VARIANTS.has(spec.variant)) {
    errors.push("variant musí být score, audit nebo plan");
  }
  if (spec.mode !== "automatizovany_prodej") {
    errors.push('mode musí být "automatizovany_prodej"');
  }
  if (spec.contact_position !== "end") {
    errors.push('contact_position musí být "end"');
  }

  if (!isNonEmptyString(spec.ghl_location_id)) {
    errors.push("ghl_location_id je povinné");
  } else if (locationId && spec.ghl_location_id !== locationId) {
    errors.push("ghl_location_id nesouhlasí s runtime GHL_LOCATION_ID");
  }

  for (const key of ["name", "cta_url", "privacy_email", "email_footer"]) {
    if (!isNonEmptyString(spec.brand?.[key])) {
      errors.push(`brand.${key} je povinné`);
    }
  }
  if (isNonEmptyString(spec.brand?.cta_url)) {
    try {
      const url = new URL(spec.brand.cta_url);
      if (!["http:", "https:"].includes(url.protocol)) throw new Error();
    } catch {
      errors.push("brand.cta_url musí být platná HTTP(S) URL");
    }
  }
  if (
    isNonEmptyString(spec.brand?.privacy_email) &&
    !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(spec.brand.privacy_email)
  ) {
    errors.push("brand.privacy_email musí být platný e-mail");
  }

  const personaFields = Array.isArray(spec.persona_fields)
    ? spec.persona_fields.filter(isNonEmptyString)
    : [];
  if (personaFields.length !== new Set(personaFields).size) {
    errors.push("persona_fields nesmí obsahovat duplicity");
  }
  for (const field of REQUIRED_PERSONA_FIELDS) {
    if (!personaFields.includes(field)) {
      errors.push(`persona_fields chybí povinné pole ${field}`);
    }
  }

  const middle = Array.isArray(spec.magnet_middle) ? spec.magnet_middle : [];
  if (middle.length < 3 || middle.length > 5) {
    errors.push("magnet_middle musí mít 3 až 5 analytických bloků");
  }
  const middleKeys = new Set();
  const middleFields = new Set();
  for (const [index, block] of middle.entries()) {
    const prefix = `magnet_middle[${index}]`;
    if (!isNonEmptyString(block?.key) || middleKeys.has(block.key)) {
      errors.push(`${prefix}.key musí být neprázdné a unikátní`);
    } else {
      middleKeys.add(block.key);
    }
    if (!isNonEmptyString(block?.title)) {
      errors.push(`${prefix}.title je povinné`);
    }
    if (!SUPPORTED_MIDDLE_RENDERS.has(block?.render)) {
      errors.push(`${prefix}.render musí být text, cards nebo steps`);
    }
    if (
      !isNonEmptyString(block?.persona_field) ||
      middleFields.has(block.persona_field)
    ) {
      errors.push(`${prefix}.persona_field musí být neprázdné a unikátní`);
    } else {
      middleFields.add(block.persona_field);
      if (!personaFields.includes(block.persona_field)) {
        errors.push(`${prefix}.persona_field chybí v persona_fields`);
      }
    }
    if (block?.persona_field === "magnet_akce") {
      errors.push(`${prefix} nesmí používat akční pole magnet_akce`);
    }
  }

  if (!Array.isArray(spec.questions) || spec.questions.length === 0) {
    errors.push("questions musí obsahovat alespoň jednu otázku");
  } else {
    for (const [index, question] of spec.questions.entries()) {
      if (!isNonEmptyString(question?.field_id)) {
        errors.push(`questions[${index}].field_id musí před deployem obsahovat GHL ID`);
      }
    }
  }
  if (!isNonEmptyString(spec.consent_field_id)) {
    errors.push("consent_field_id musí před deployem obsahovat GHL ID");
  }

  const placeholders = collectPlaceholderPaths(spec);
  if (placeholders.length > 0) {
    errors.push(
      `spec obsahuje zástupné hodnoty: ${placeholders.slice(0, 8).join(", ")}`
    );
  }
  return errors;
}

export { REQUIRED_PERSONA_FIELDS };
