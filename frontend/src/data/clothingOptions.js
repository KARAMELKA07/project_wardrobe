const normalizeValue = (value) =>
  String(value || "")
    .trim()
    .toLowerCase()
    .replace(/-/g, "_")
    .replace(/\s+/g, "_");

const SHOE_SUBCATEGORY_ALIAS_MAP = {
  winter_boots: "boots",
  felt_boots: "boots",
  warm_boots: "boots",
  demi_boots: "boots",
  closed_shoes: "shoes",
  loafers: "shoes",
  summer_sneakers: "sneakers",
  espadrilles: "shoes",
  flip_flops: "slippers",
  heels: "pumps",
  high_heels: "pumps",
};

export const CATEGORY_OPTIONS = [
  { value: "top", label: "Верх" },
  { value: "dress", label: "Платья" },
  { value: "bottom", label: "Низ" },
  { value: "shoes", label: "Обувь" },
  { value: "outerwear", label: "Верхняя одежда" },
  { value: "accessory", label: "Аксессуары" },
];

export const SUBCATEGORY_OPTIONS = {
  top: [
    { value: "t_shirt", label: "Футболка" },
    { value: "shirt", label: "Рубашка" },
    { value: "top", label: "Топ" },
    { value: "kurta", label: "Курта" },
    { value: "sweater", label: "Свитер" },
    { value: "sweatshirt", label: "Свитшот" },
    { value: "tunic", label: "Туника" },
    { value: "underwear", label: "Нижнее белье" },
    { value: "sleepwear", label: "Одежда для сна" },
  ],
  dress: [{ value: "dress", label: "Платье" }],
  bottom: [
    { value: "jeans", label: "Джинсы" },
    { value: "trousers", label: "Брюки" },
    { value: "joggers", label: "Джоггеры" },
    { value: "leggings", label: "Леггинсы" },
    { value: "shorts", label: "Шорты" },
    { value: "skirt", label: "Юбка" },
  ],
  shoes: [
    { value: "shoes", label: "Обувь" },
    { value: "sneakers", label: "Кроссовки" },
    { value: "sandals", label: "Сандалии" },
  ],
  outerwear: [{ value: "jacket", label: "Куртка" }],
  accessory: [
    { value: "bag", label: "Сумка" },
    { value: "wallet", label: "Кошелек" },
    { value: "belt", label: "Ремень" },
    { value: "watch", label: "Часы" },
    { value: "sunglasses", label: "Солнцезащитные очки" },
    { value: "hat", label: "Головной убор" },
    { value: "scarf", label: "Шарф" },
    { value: "socks", label: "Носки" },
    { value: "jewelry", label: "Украшение" },
    { value: "bracelet", label: "Браслет" },
    { value: "earrings", label: "Серьги" },
    { value: "necklace", label: "Ожерелье" },
    { value: "tie", label: "Галстук" },
  ],
};

export const ZAPPOS_SHOE_OPTIONS = [
  { value: "shoes", label: "Обувь" },
  { value: "ankle_boots", label: "Ботильоны" },
  { value: "boots", label: "Ботинки" },
  { value: "flats", label: "Балетки" },
  { value: "pumps", label: "Туфли" },
  { value: "sandals", label: "Сандалии" },
  { value: "slippers", label: "Сланцы" },
  { value: "sneakers", label: "Кроссовки" },
];

export const STYLE_OPTIONS = [
  { value: "basic", label: "Базовый" },
  { value: "minimal", label: "Минимализм" },
  { value: "casual", label: "Повседневный" },
  { value: "classic", label: "Классика" },
  { value: "business", label: "Деловой" },
  { value: "sport", label: "Спортивный" },
  { value: "street", label: "Стритстайл" },
  { value: "evening", label: "Вечерний" },
  { value: "party", label: "Для вечеринки" },
  { value: "statement", label: "Акцентный" },
];

export const COLOR_OPTIONS = [
  { value: "white", label: "Белый", hex: "#f6f3ec", border: "#d8d2c7" },
  { value: "cream", label: "Кремовый", hex: "#f3e8d8", border: "#dbcab1" },
  { value: "black", label: "Черный", hex: "#171717", border: "#171717" },
  { value: "silver", label: "Серебристый", hex: "#c8ccd6", border: "#aeb5c1" },
  { value: "gray", label: "Серый", hex: "#8d939b", border: "#7b8188" },
  { value: "beige", label: "Бежевый", hex: "#dcc7a1", border: "#c2ab82" },
  { value: "camel", label: "Кэмел", hex: "#b78753", border: "#9e7141" },
  { value: "brown", label: "Коричневый", hex: "#8b5a3c", border: "#6d442c" },
  { value: "blue", label: "Синий", hex: "#4c84d9", border: "#3f6fbb" },
  { value: "navy", label: "Темно-синий", hex: "#1d3764", border: "#1d3764" },
  { value: "turquoise", label: "Бирюзовый", hex: "#48b8c7", border: "#3a9ba8" },
  { value: "green", label: "Зеленый", hex: "#4e8c62", border: "#3f724f" },
  { value: "olive", label: "Оливковый", hex: "#7b8450", border: "#697145" },
  { value: "red", label: "Красный", hex: "#cf4e4e", border: "#b43c3c" },
  { value: "burgundy", label: "Бордовый", hex: "#7a2f41", border: "#662838" },
  { value: "yellow", label: "Желтый", hex: "#ebcb53", border: "#cfb244" },
  { value: "orange", label: "Оранжевый", hex: "#ef9551", border: "#d97c37" },
  { value: "pink", label: "Розовый", hex: "#e6a6bd", border: "#cf90a7" },
  { value: "lavender", label: "Лавандовый", hex: "#b8a5df", border: "#a18acc" },
  { value: "purple", label: "Фиолетовый", hex: "#8d6bc7", border: "#7958b2" },
];

export const FIT_OPTIONS = [
  { value: "fitted", label: "Приталенная" },
  { value: "balanced", label: "Сбалансированная" },
  { value: "loose", label: "Свободная" },
  { value: "oversized", label: "Оверсайз" },
];

export const LAYER_LEVEL_OPTIONS = [
  { value: "base", label: "Базовый слой" },
  { value: "mid", label: "Утепляющий слой" },
  { value: "outer", label: "Верхний слой" },
  { value: "support", label: "Аксессуар" },
];

export const INSULATION_OPTIONS = [
  { value: "0.2", label: "Очень легкая" },
  { value: "0.6", label: "Легкая" },
  { value: "1.0", label: "Умеренная" },
  { value: "1.5", label: "Теплая" },
  { value: "2.0", label: "Очень теплая" },
  { value: "2.6", label: "Для сильного холода" },
];

const DEFAULT_FIT_BY_SUBCATEGORY = {
  t_shirt: "balanced",
  shirt: "fitted",
  top: "fitted",
  kurta: "balanced",
  dress: "balanced",
  sweater: "loose",
  sweatshirt: "loose",
  tunic: "balanced",
  underwear: "fitted",
  sleepwear: "loose",
  jeans: "balanced",
  trousers: "fitted",
  joggers: "loose",
  leggings: "fitted",
  shorts: "balanced",
  skirt: "balanced",
  shoes: "balanced",
  sneakers: "balanced",
  sandals: "fitted",
  jacket: "balanced",
  bag: "balanced",
  wallet: "balanced",
  belt: "fitted",
  watch: "fitted",
  sunglasses: "balanced",
  hat: "balanced",
  scarf: "loose",
  socks: "fitted",
  jewelry: "fitted",
  bracelet: "fitted",
  earrings: "fitted",
  necklace: "fitted",
  tie: "fitted",
};

Object.assign(DEFAULT_FIT_BY_SUBCATEGORY, {
  ankle_boots: "fitted",
  boots: "balanced",
  flats: "fitted",
  pumps: "fitted",
  slippers: "loose",
});

const SUBCATEGORY_GRAMMAR = {
  t_shirt: { noun: "футболка", gender: "f" },
  shirt: { noun: "рубашка", gender: "f" },
  top: { noun: "топ", gender: "m" },
  kurta: { noun: "курта", gender: "f" },
  dress: { noun: "платье", gender: "n" },
  sweater: { noun: "свитер", gender: "m" },
  sweatshirt: { noun: "свитшот", gender: "m" },
  tunic: { noun: "туника", gender: "f" },
  underwear: { noun: "нижнее белье", gender: "n" },
  sleepwear: { noun: "одежда для сна", gender: "f" },
  jeans: { noun: "джинсы", gender: "pl" },
  trousers: { noun: "брюки", gender: "pl" },
  joggers: { noun: "джоггеры", gender: "pl" },
  leggings: { noun: "леггинсы", gender: "pl" },
  shorts: { noun: "шорты", gender: "pl" },
  skirt: { noun: "юбка", gender: "f" },
  shoes: { noun: "обувь", gender: "f" },
  sneakers: { noun: "кроссовки", gender: "pl" },
  sandals: { noun: "сандалии", gender: "pl" },
  jacket: { noun: "куртка", gender: "f" },
  bag: { noun: "сумка", gender: "f" },
  wallet: { noun: "кошелек", gender: "m" },
  belt: { noun: "ремень", gender: "m" },
  watch: { noun: "часы", gender: "pl" },
  sunglasses: { noun: "солнцезащитные очки", gender: "pl" },
  hat: { noun: "головной убор", gender: "m" },
  scarf: { noun: "шарф", gender: "m" },
  socks: { noun: "носки", gender: "pl" },
  jewelry: { noun: "украшение", gender: "n" },
  bracelet: { noun: "браслет", gender: "m" },
  earrings: { noun: "серьги", gender: "pl" },
  necklace: { noun: "ожерелье", gender: "n" },
  tie: { noun: "галстук", gender: "m" },
};

Object.assign(SUBCATEGORY_GRAMMAR, {
  ankle_boots: { noun: "ботильоны", gender: "pl" },
  boots: { noun: "ботинки", gender: "pl" },
  flats: { noun: "балетки", gender: "pl" },
  pumps: { noun: "туфли", gender: "pl" },
  slippers: { noun: "сланцы", gender: "pl" },
});

const COLOR_ADJECTIVES = {
  white: { m: "белый", f: "белая", n: "белое", pl: "белые" },
  cream: { m: "кремовый", f: "кремовая", n: "кремовое", pl: "кремовые" },
  black: { m: "черный", f: "черная", n: "черное", pl: "черные" },
  silver: { m: "серебристый", f: "серебристая", n: "серебристое", pl: "серебристые" },
  gray: { m: "серый", f: "серая", n: "серое", pl: "серые" },
  beige: { m: "бежевый", f: "бежевая", n: "бежевое", pl: "бежевые" },
  camel: { m: "кэмел", f: "кэмел", n: "кэмел", pl: "кэмел" },
  brown: { m: "коричневый", f: "коричневая", n: "коричневое", pl: "коричневые" },
  blue: { m: "синий", f: "синяя", n: "синее", pl: "синие" },
  navy: { m: "темно-синий", f: "темно-синяя", n: "темно-синее", pl: "темно-синие" },
  turquoise: { m: "бирюзовый", f: "бирюзовая", n: "бирюзовое", pl: "бирюзовые" },
  green: { m: "зеленый", f: "зеленая", n: "зеленое", pl: "зеленые" },
  olive: { m: "оливковый", f: "оливковая", n: "оливковое", pl: "оливковые" },
  red: { m: "красный", f: "красная", n: "красное", pl: "красные" },
  burgundy: { m: "бордовый", f: "бордовая", n: "бордовое", pl: "бордовые" },
  yellow: { m: "желтый", f: "желтая", n: "желтое", pl: "желтые" },
  orange: { m: "оранжевый", f: "оранжевая", n: "оранжевое", pl: "оранжевые" },
  pink: { m: "розовый", f: "розовая", n: "розовое", pl: "розовые" },
  lavender: { m: "лавандовый", f: "лавандовая", n: "лавандовое", pl: "лавандовые" },
  purple: { m: "фиолетовый", f: "фиолетовая", n: "фиолетовое", pl: "фиолетовые" },
};

const DEFAULT_LAYER_LEVEL_BY_SUBCATEGORY = {
  t_shirt: "base",
  shirt: "base",
  top: "base",
  kurta: "base",
  dress: "base",
  tunic: "base",
  underwear: "base",
  sleepwear: "base",
  sweater: "mid",
  sweatshirt: "mid",
  jacket: "outer",
  bag: "support",
  wallet: "support",
  belt: "support",
  watch: "support",
  sunglasses: "support",
  hat: "support",
  scarf: "support",
  socks: "support",
  jewelry: "support",
  bracelet: "support",
  earrings: "support",
  necklace: "support",
  tie: "support",
};

const DEFAULT_INSULATION_BY_SUBCATEGORY = {
  t_shirt: "0.6",
  shirt: "0.8",
  top: "0.5",
  kurta: "0.8",
  dress: "0.8",
  sweater: "1.8",
  sweatshirt: "1.5",
  tunic: "0.8",
  underwear: "0.2",
  sleepwear: "0.6",
  jeans: "1.4",
  trousers: "1.2",
  joggers: "1.4",
  leggings: "1.0",
  shorts: "0.3",
  skirt: "0.8",
  shoes: "0.8",
  sneakers: "0.9",
  sandals: "0.2",
  jacket: "1.7",
  scarf: "0.5",
  hat: "0.4",
  socks: "0.3",
};

Object.assign(DEFAULT_INSULATION_BY_SUBCATEGORY, {
  ankle_boots: "1.4",
  boots: "1.5",
  flats: "0.7",
  pumps: "0.8",
  slippers: "0.1",
});

const WATERPROOF_SUBCATEGORIES = new Set(["jacket"]);
const WINDPROOF_SUBCATEGORIES = new Set(["jacket"]);

const SUBCATEGORY_LABELS = Object.values(SUBCATEGORY_OPTIONS)
  .flat()
  .reduce((acc, entry) => {
    acc[entry.value] = entry.label;
    return acc;
  }, {});

ZAPPOS_SHOE_OPTIONS.forEach((entry) => {
  SUBCATEGORY_LABELS[entry.value] = entry.label;
});

const STYLE_LABELS = STYLE_OPTIONS.reduce((acc, entry) => {
  acc[entry.value] = entry.label;
  return acc;
}, {});

const COLOR_LABELS = COLOR_OPTIONS.reduce((acc, entry) => {
  acc[entry.value] = entry.label;
  return acc;
}, {});

const FIT_LABELS = FIT_OPTIONS.reduce((acc, entry) => {
  acc[entry.value] = entry.label;
  return acc;
}, {});

const LAYER_LEVEL_LABELS = LAYER_LEVEL_OPTIONS.reduce((acc, entry) => {
  acc[entry.value] = entry.label;
  return acc;
}, {});

const ITEM_METADATA_SUPPORT = {
  top: {
    supportsFit: true,
    supportsLayerLevel: true,
    supportsInsulation: true,
    supportsWaterproof: false,
    supportsWindproof: false,
  },
  dress: {
    supportsFit: true,
    supportsLayerLevel: true,
    supportsInsulation: true,
    supportsWaterproof: false,
    supportsWindproof: false,
  },
  bottom: {
    supportsFit: true,
    supportsLayerLevel: false,
    supportsInsulation: true,
    supportsWaterproof: false,
    supportsWindproof: false,
  },
  shoes: {
    supportsFit: false,
    supportsLayerLevel: false,
    supportsInsulation: true,
    supportsWaterproof: true,
    supportsWindproof: false,
  },
  outerwear: {
    supportsFit: true,
    supportsLayerLevel: true,
    supportsInsulation: true,
    supportsWaterproof: true,
    supportsWindproof: true,
  },
  accessory: {
    supportsFit: false,
    supportsLayerLevel: false,
    supportsInsulation: false,
    supportsWaterproof: false,
    supportsWindproof: false,
  },
};

export function normalizeCatalogValue(value) {
  const normalizedValue = normalizeValue(value);
  return SHOE_SUBCATEGORY_ALIAS_MAP[normalizedValue] || normalizedValue;
}

export function getSubcategoryOptions(category) {
  const normalizedCategory = normalizeCatalogValue(category);
  if (normalizedCategory === "shoes") {
    return ZAPPOS_SHOE_OPTIONS;
  }
  return SUBCATEGORY_OPTIONS[normalizedCategory] || [];
}

export function getSubcategoryLabel(value) {
  return SUBCATEGORY_LABELS[normalizeCatalogValue(value)] || value || "";
}

export function getStyleLabel(value) {
  return STYLE_LABELS[normalizeValue(value)] || value || "";
}

export function getColorLabel(value) {
  return COLOR_LABELS[normalizeValue(value)] || value || "";
}

export function getFitLabel(value) {
  return FIT_LABELS[normalizeValue(value)] || value || "";
}

export function getLayerLevelLabel(value) {
  return LAYER_LEVEL_LABELS[normalizeValue(value)] || value || "";
}

export function getItemMetadataSupport(category) {
  return (
    ITEM_METADATA_SUPPORT[normalizeCatalogValue(category)] || {
      supportsFit: false,
      supportsLayerLevel: false,
      supportsInsulation: false,
      supportsWaterproof: false,
      supportsWindproof: false,
    }
  );
}

export function getDefaultFitValue(subcategory) {
  return DEFAULT_FIT_BY_SUBCATEGORY[normalizeCatalogValue(subcategory)] || "balanced";
}

export function getDefaultLayerLevelValue(subcategory, category) {
  const normalizedSubcategory = normalizeCatalogValue(subcategory);
  if (DEFAULT_LAYER_LEVEL_BY_SUBCATEGORY[normalizedSubcategory]) {
    return DEFAULT_LAYER_LEVEL_BY_SUBCATEGORY[normalizedSubcategory];
  }

  const normalizedCategory = normalizeCatalogValue(category);
  if (normalizedCategory === "dress") {
    return "base";
  }
  if (normalizedCategory === "outerwear") {
    return "outer";
  }
  if (normalizedCategory === "accessory") {
    return "support";
  }
  return "base";
}

export function buildRussianItemTitle(color, subcategory, fallbackTitle = "вещь") {
  const normalizedSubcategory = normalizeCatalogValue(subcategory);
  const grammar = SUBCATEGORY_GRAMMAR[normalizedSubcategory] || {
    noun: String(fallbackTitle || "вещь").toLowerCase(),
    gender: "f",
  };
  const adjective = COLOR_ADJECTIVES[normalizeValue(color)]?.[grammar.gender];
  return [adjective, grammar.noun].filter(Boolean).join(" ").trim();
}

export function getDefaultInsulationValue(subcategory) {
  return DEFAULT_INSULATION_BY_SUBCATEGORY[normalizeCatalogValue(subcategory)] || "0.6";
}

export function getDefaultProtectionFlags(subcategory) {
  const normalizedSubcategory = normalizeCatalogValue(subcategory);
  return {
    waterproof: WATERPROOF_SUBCATEGORIES.has(normalizedSubcategory),
    windproof: WINDPROOF_SUBCATEGORIES.has(normalizedSubcategory),
  };
}

export function buildItemMetadataDefaults(category, subcategory) {
  const support = getItemMetadataSupport(category);
  const protectionFlags = getDefaultProtectionFlags(subcategory);

  return {
    fit: support.supportsFit ? getDefaultFitValue(subcategory) : "",
    layer_level: support.supportsLayerLevel
      ? getDefaultLayerLevelValue(subcategory, category)
      : "",
    insulation_rating: support.supportsInsulation
      ? getDefaultInsulationValue(subcategory)
      : "0",
    waterproof: support.supportsWaterproof ? protectionFlags.waterproof : false,
    windproof: support.supportsWindproof ? protectionFlags.windproof : false,
  };
}

export function sanitizeItemMetadata(category, subcategory, values = {}) {
  const defaults = buildItemMetadataDefaults(category, subcategory);
  const support = getItemMetadataSupport(category);

  return {
    fit: support.supportsFit ? values.fit || defaults.fit : "",
    layer_level: support.supportsLayerLevel
      ? values.layer_level || defaults.layer_level
      : "",
    insulation_rating: support.supportsInsulation
      ? String(values.insulation_rating ?? defaults.insulation_rating)
      : "0",
    waterproof: support.supportsWaterproof
      ? Boolean(values.waterproof ?? defaults.waterproof)
      : false,
    windproof: support.supportsWindproof
      ? Boolean(values.windproof ?? defaults.windproof)
      : false,
  };
}
