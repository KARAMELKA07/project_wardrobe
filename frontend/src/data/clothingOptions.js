const normalizeValue = (value) =>
  String(value || "")
    .trim()
    .toLowerCase()
    .replace(/-/g, "_")
    .replace(/\s+/g, "_");

export const CATEGORY_OPTIONS = [
  { value: "top", label: "Верх" },
  { value: "bottom", label: "Низ" },
  { value: "shoes", label: "Обувь" },
  { value: "outerwear", label: "Верхний слой" },
  { value: "accessory", label: "Аксессуар" },
];

export const SUBCATEGORY_OPTIONS = {
  top: [
    { value: "t_shirt", label: "Футболка" },
    { value: "shirt", label: "Рубашка" },
    { value: "blouse", label: "Блузка" },
    { value: "polo", label: "Поло" },
    { value: "longsleeve", label: "Лонгслив" },
    { value: "sweater", label: "Свитер" },
    { value: "hoodie", label: "Худи" },
    { value: "cardigan", label: "Кардиган" },
    { value: "turtleneck", label: "Водолазка" },
    { value: "sweatshirt", label: "Свитшот" },
    { value: "vest", label: "Жилет" },
    { value: "crop_top", label: "Кроп-топ" },
  ],
  bottom: [
    { value: "jeans", label: "Джинсы" },
    { value: "trousers", label: "Брюки" },
    { value: "chinos", label: "Чиносы" },
    { value: "joggers", label: "Джоггеры" },
    { value: "leggings", label: "Леггинсы" },
    { value: "culottes", label: "Кюлоты" },
    { value: "skirt", label: "Юбка" },
    { value: "mini_skirt", label: "Мини-юбка" },
    { value: "midi_skirt", label: "Миди-юбка" },
    { value: "maxi_skirt", label: "Макси-юбка" },
    { value: "shorts", label: "Шорты" },
  ],
  shoes: [
    { value: "winter_boots", label: "Зимние сапоги" },
    { value: "felt_boots", label: "Валенки" },
    { value: "warm_boots", label: "Теплые ботинки" },
    { value: "demi_boots", label: "Демисезонные ботинки" },
    { value: "ankle_boots", label: "Ботильоны" },
    { value: "boots", label: "Ботинки" },
    { value: "closed_shoes", label: "Закрытые туфли" },
    { value: "pumps", label: "Туфли" },
    { value: "loafers", label: "Лоферы" },
    { value: "sneakers", label: "Кроссовки" },
    { value: "summer_sneakers", label: "Летние кроссовки" },
    { value: "sandals", label: "Босоножки" },
    { value: "espadrilles", label: "Эспадрильи" },
    { value: "flip_flops", label: "Шлепки" },
    { value: "slippers", label: "Сланцы" },
  ],
  outerwear: [
    { value: "coat", label: "Пальто" },
    { value: "jacket", label: "Куртка" },
    { value: "parka", label: "Парка" },
    { value: "down_jacket", label: "Пуховик" },
    { value: "trench", label: "Тренч" },
    { value: "blazer", label: "Пиджак" },
    { value: "leather_jacket", label: "Кожаная куртка" },
    { value: "windbreaker", label: "Ветровка" },
    { value: "vest_outerwear", label: "Жилет" },
  ],
  accessory: [
    { value: "bag", label: "Сумка" },
    { value: "backpack", label: "Рюкзак" },
    { value: "scarf", label: "Шарф" },
    { value: "hat", label: "Шапка" },
    { value: "cap", label: "Кепка" },
    { value: "gloves", label: "Перчатки" },
    { value: "belt", label: "Ремень" },
    { value: "jewelry", label: "Украшение" },
  ],
};

export const STYLE_OPTIONS = [
  { value: "basic", label: "Базовый" },
  { value: "minimal", label: "Минимализм" },
  { value: "casual", label: "Повседневный" },
  { value: "classic", label: "Классика" },
  { value: "business", label: "Деловой" },
  { value: "sport", label: "Спортивный" },
  { value: "athleisure", label: "Спорт-шик" },
  { value: "street", label: "Стритстайл" },
  { value: "romantic", label: "Романтичный" },
  { value: "evening", label: "Вечерний" },
  { value: "party", label: "Для вечеринки" },
  { value: "fashion", label: "Трендовый" },
  { value: "statement", label: "Акцентный" },
  { value: "boho", label: "Бохо" },
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
  { value: "support", label: "Поддерживающий аксессуар" },
];

export const INSULATION_OPTIONS = [
  { value: "0.2", label: "Очень лёгкая" },
  { value: "0.6", label: "Лёгкая" },
  { value: "1.0", label: "Умеренная" },
  { value: "1.5", label: "Тёплая" },
  { value: "2.0", label: "Очень тёплая" },
  { value: "2.6", label: "Для сильного холода" },
];

const DEFAULT_FIT_BY_SUBCATEGORY = {
  t_shirt: "balanced",
  shirt: "fitted",
  blouse: "fitted",
  polo: "balanced",
  longsleeve: "balanced",
  sweater: "loose",
  hoodie: "oversized",
  cardigan: "loose",
  turtleneck: "fitted",
  sweatshirt: "loose",
  vest: "balanced",
  crop_top: "fitted",
  jeans: "balanced",
  trousers: "fitted",
  chinos: "balanced",
  joggers: "loose",
  leggings: "fitted",
  culottes: "loose",
  skirt: "balanced",
  mini_skirt: "fitted",
  midi_skirt: "balanced",
  maxi_skirt: "loose",
  shorts: "balanced",
  winter_boots: "balanced",
  felt_boots: "balanced",
  warm_boots: "balanced",
  demi_boots: "balanced",
  ankle_boots: "fitted",
  boots: "balanced",
  closed_shoes: "fitted",
  pumps: "fitted",
  loafers: "fitted",
  sneakers: "balanced",
  summer_sneakers: "balanced",
  sandals: "fitted",
  espadrilles: "balanced",
  flip_flops: "loose",
  slippers: "loose",
  coat: "balanced",
  jacket: "balanced",
  parka: "oversized",
  down_jacket: "oversized",
  trench: "balanced",
  blazer: "fitted",
  leather_jacket: "balanced",
  windbreaker: "loose",
  vest_outerwear: "balanced",
  bag: "balanced",
  backpack: "balanced",
  scarf: "loose",
  hat: "balanced",
  cap: "balanced",
  gloves: "fitted",
  belt: "fitted",
  jewelry: "fitted",
};

const DEFAULT_LAYER_LEVEL_BY_SUBCATEGORY = {
  t_shirt: "base",
  shirt: "base",
  blouse: "base",
  polo: "base",
  longsleeve: "base",
  crop_top: "base",
  turtleneck: "base",
  sweater: "mid",
  hoodie: "mid",
  cardigan: "mid",
  sweatshirt: "mid",
  vest: "mid",
  coat: "outer",
  jacket: "outer",
  parka: "outer",
  down_jacket: "outer",
  trench: "outer",
  blazer: "outer",
  leather_jacket: "outer",
  windbreaker: "outer",
  vest_outerwear: "outer",
  bag: "support",
  backpack: "support",
  scarf: "support",
  hat: "support",
  cap: "support",
  gloves: "support",
  belt: "support",
  jewelry: "support",
};

const DEFAULT_INSULATION_BY_SUBCATEGORY = {
  t_shirt: "0.6",
  shirt: "0.8",
  blouse: "0.7",
  polo: "0.7",
  longsleeve: "1.0",
  crop_top: "0.2",
  sweater: "1.8",
  hoodie: "1.7",
  cardigan: "1.4",
  turtleneck: "1.5",
  sweatshirt: "1.5",
  vest: "1.1",
  jeans: "1.4",
  trousers: "1.2",
  chinos: "1.1",
  joggers: "1.4",
  leggings: "1.0",
  culottes: "0.9",
  skirt: "0.8",
  mini_skirt: "0.5",
  midi_skirt: "0.8",
  maxi_skirt: "0.9",
  shorts: "0.3",
  winter_boots: "2.0",
  felt_boots: "2.2",
  warm_boots: "1.9",
  demi_boots: "1.5",
  ankle_boots: "1.4",
  boots: "1.3",
  closed_shoes: "1.0",
  pumps: "0.8",
  loafers: "0.8",
  sneakers: "0.9",
  summer_sneakers: "0.6",
  sandals: "0.2",
  espadrilles: "0.3",
  flip_flops: "0.1",
  slippers: "0.1",
  coat: "2.4",
  jacket: "1.7",
  parka: "2.6",
  down_jacket: "2.8",
  trench: "1.5",
  blazer: "1.2",
  leather_jacket: "1.6",
  windbreaker: "1.2",
  vest_outerwear: "1.2",
  scarf: "0.5",
  hat: "0.4",
  gloves: "0.4",
};

const WATERPROOF_SUBCATEGORIES = new Set([
  "trench",
  "parka",
  "down_jacket",
  "windbreaker",
  "jacket",
]);

const WINDPROOF_SUBCATEGORIES = new Set([
  "coat",
  "parka",
  "down_jacket",
  "windbreaker",
  "leather_jacket",
]);

const SUBCATEGORY_LABELS = Object.values(SUBCATEGORY_OPTIONS).flat().reduce((acc, entry) => {
  acc[entry.value] = entry.label;
  return acc;
}, {});

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

export function normalizeCatalogValue(value) {
  return normalizeValue(value);
}

export function getSubcategoryOptions(category) {
  return SUBCATEGORY_OPTIONS[normalizeValue(category)] || [];
}

export function getSubcategoryLabel(value) {
  return SUBCATEGORY_LABELS[normalizeValue(value)] || value || "";
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

export function getDefaultFitValue(subcategory) {
  return DEFAULT_FIT_BY_SUBCATEGORY[normalizeValue(subcategory)] || "balanced";
}

export function getDefaultLayerLevelValue(subcategory, category) {
  const normalizedSubcategory = normalizeValue(subcategory);
  if (DEFAULT_LAYER_LEVEL_BY_SUBCATEGORY[normalizedSubcategory]) {
    return DEFAULT_LAYER_LEVEL_BY_SUBCATEGORY[normalizedSubcategory];
  }

  const normalizedCategory = normalizeValue(category);
  if (normalizedCategory === "outerwear") {
    return "outer";
  }
  if (normalizedCategory === "accessory") {
    return "support";
  }
  return "base";
}

export function getDefaultInsulationValue(subcategory) {
  return DEFAULT_INSULATION_BY_SUBCATEGORY[normalizeValue(subcategory)] || "0.6";
}

export function getDefaultProtectionFlags(subcategory) {
  const normalizedSubcategory = normalizeValue(subcategory);
  return {
    waterproof: WATERPROOF_SUBCATEGORIES.has(normalizedSubcategory),
    windproof: WINDPROOF_SUBCATEGORIES.has(normalizedSubcategory),
  };
}
