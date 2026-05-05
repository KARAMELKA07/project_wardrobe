## Рисунок 2.4 — ER-диаграмма проектируемой базы данных

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "background": "#ffffff",
    "primaryColor": "#ffffff",
    "primaryTextColor": "#000000",
    "primaryBorderColor": "#000000",
    "lineColor": "#000000",
    "secondaryColor": "#ffffff",
    "secondaryTextColor": "#000000",
    "secondaryBorderColor": "#000000",
    "tertiaryColor": "#ffffff",
    "tertiaryTextColor": "#000000",
    "tertiaryBorderColor": "#000000"
  }
}}%%
erDiagram
    USERS ||--|| USER_PREFERENCES : has
    USERS ||--o{ CLOTHING_ITEMS : owns
    USERS ||--o{ OUTFITS : saves
    USERS ||--o{ OUTFIT_FEEDBACK : leaves

    OUTFITS ||--o{ OUTFIT_ITEMS : contains
    OUTFITS ||--o{ OUTFIT_FEEDBACK : receives
    CLOTHING_ITEMS ||--o{ OUTFIT_ITEMS : participates

    USERS {
        int id PK
        string email
        string password_hash
        string name
        string city
    }

    USER_PREFERENCES {
        int id PK
        int user_id FK
        json preferred_styles
        json preferred_colors
        json constraints
        json disliked_items
    }

    CLOTHING_ITEMS {
        int id PK
        int user_id FK
        string image_url
        string title
        string category
        string subcategory
        json colors
        json styles
        string season
        string formality
        string fit
        string layer_level
        float insulation_rating
        bool waterproof
        bool windproof
        string material
    }

    OUTFITS {
        int id PK
        int user_id FK
        string name
        string event_type
        json weather_context
        float score
        text explanation
        json feature_scores
        json reasons
        string styled_photo_url
    }

    OUTFIT_ITEMS {
        int id PK
        int outfit_id FK
        int clothing_item_id FK
        string role
    }

    OUTFIT_FEEDBACK {
        int id PK
        int outfit_id FK
        int user_id FK
        string reaction
    }
```

### Подпись к рисунку

На рисунке представлена ER-диаграмма проектируемой базы данных веб-сервиса подбора образов. Диаграмма отражает основные сущности предметной области, их атрибуты, первичные и внешние ключи, а также логические связи между таблицами. В центре модели располагается сущность пользователя, так как именно через нее определяется принадлежность остальных данных системы. Через пользователя связываются предпочтения, элементы цифрового гардероба, сохраненные образы и записи обратной связи. Для представления состава образа используется отдельная промежуточная сущность `OUTFIT_ITEMS`, которая реализует связь между образом и вещами.

### Что важно при переносе схемы в диплом

- для `USERS` и `USER_PREFERENCES` следует показывать связь `1:1`;
- для `USERS` и `CLOTHING_ITEMS` используется связь `1:N`;
- для `USERS` и `OUTFITS` используется связь `1:N`;
- связь между `OUTFITS` и `CLOTHING_ITEMS` реализуется не напрямую, а через `OUTFIT_ITEMS`;
- в `OUTFIT_FEEDBACK` желательно отдельно подписать ограничение уникальности пары `outfit_id + user_id`;
- в `USER_PREFERENCES` желательно отдельно подписать уникальность `user_id`;
- в `USERS` желательно отдельно подписать уникальность `email`.

### Важная корректировка схемы

В таблице `OUTFITS` не следует добавлять поля `outfit_id` или `string_image_item_id`. Для проектируемой модели корректным является набор полей: идентификатор образа, ссылка на пользователя, название, тип события, погодный контекст, итоговая оценка, пояснение, оценки по признакам, причины выбора и путь к фотографии пользователя в образе.
