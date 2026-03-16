from collections import Counter


class WardrobeAnalyticsService:
    @staticmethod
    def build_summary(items):
        category_counts = Counter()
        season_counts = Counter()
        style_counts = Counter()

        for item in items:
            category_counts[item.category] += 1
            season_counts[item.season] += 1
            for style in item.styles or []:
                style_counts[style] += 1

        return {
            "total_items": len(items),
            "by_category": dict(category_counts),
            "by_season": dict(season_counts),
            "by_style": dict(style_counts),
            "recommendations": WardrobeAnalyticsService.build_recommendations(
                len(items),
                category_counts,
                season_counts,
                style_counts,
            ),
        }

    @staticmethod
    def build_recommendations(total_items, category_counts, season_counts, style_counts):
        recommendations = []

        if category_counts.get("shoes", 0) < 2:
            recommendations.append("У вас мало обуви.")
        if category_counts.get("outerwear", 0) < 1:
            recommendations.append("В гардеробе мало верхней одежды.")
        if total_items and max(season_counts.values(), default=0) / total_items >= 0.6:
            recommendations.append(
                "Большинство вещей относится к одному сезону. Гардероб стоит сбалансировать."
            )

        basic_style_count = style_counts.get("basic", 0) + style_counts.get("casual", 0)
        if basic_style_count < 3:
            recommendations.append("Недостаточно универсальных базовых вещей.")

        if category_counts.get("top", 0) < 2 or category_counts.get("bottom", 0) < 2:
            recommendations.append("Добавьте больше верха или низа для новых сочетаний.")

        if not recommendations:
            recommendations.append("Состав гардероба выглядит достаточно сбалансированным.")

        return recommendations
