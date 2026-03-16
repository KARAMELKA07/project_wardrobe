export const CATEGORY_LABELS = {
  top: "Верх",
  bottom: "Низ",
  shoes: "Обувь",
  outerwear: "Верхний слой",
  accessory: "Аксессуар",
};

export const ROLE_LABELS = {
  top: "Верх",
  bottom: "Низ",
  shoes: "Обувь",
  outerwear: "Верхний слой",
  accessory: "Аксессуар",
};

export const SEASON_LABELS = {
  "all-season": "Всесезон",
  all_season: "Всесезон",
  spring: "Весна",
  summer: "Лето",
  autumn: "Осень",
  winter: "Зима",
};

export const FORMALITY_LABELS = {
  casual: "Повседневный",
  smart: "Смарт-кэжуал",
  formal: "Формальный",
};

export const EVENT_LABELS = {
  office: "Офис",
  casual: "Повседневный",
  evening: "Вечерний",
  sport: "Спортивный",
  party: "Вечеринка",
  travel: "Поездка",
  date: "Свидание",
};

export const WEATHER_LABELS = {
  sunny: "Солнечно",
  cloudy: "Облачно",
  clear: "Ясно",
  rain: "Дождь",
  snow: "Снег",
  wind: "Ветрено",
};

export const FEATURE_LABELS = {
  color_harmony: "Гармония цветов",
  style_match: "Сочетаемость стилей",
  event_match: "Соответствие событию",
  season_match: "Соответствие сезону",
  temperature_match: "Соответствие температуре",
  weather_condition_match: "Соответствие погоде",
  completeness: "Полнота комплекта",
  layering_correctness: "Корректность слоев",
  user_preference_match: "Учет предпочтений",
  constraints_match: "Соблюдение ограничений",
};


function translate(map, value) {
  if (!value) {
    return "";
  }

  return map[String(value)] || value;
}


export function translateCategory(value) {
  return translate(CATEGORY_LABELS, value);
}


export function translateRole(value) {
  return translate(ROLE_LABELS, value);
}


export function translateSeason(value) {
  return translate(SEASON_LABELS, value);
}


export function translateFormality(value) {
  return translate(FORMALITY_LABELS, value);
}


export function translateEventType(value) {
  return translate(EVENT_LABELS, value);
}


export function translateWeather(value) {
  return translate(WEATHER_LABELS, value);
}


export function translateFeatureName(value) {
  return translate(FEATURE_LABELS, value);
}
