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
