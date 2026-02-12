import time


class NewsGeneratorService:
    def generate(self, cluster_name: str, prompt: str) -> tuple[str, str]:
        time.sleep(0.25)
        p = (prompt or "").strip() or "Стандартный промпт."

        title = f"Сгенерировано по кластеру: {cluster_name}"
        body = (
            f"Промпт: {p}\n\n"
            "После публичного заявления рынок отреагировал волатильностью. "
            "Аналитики связывают движение с пересмотром ожиданий участников и ростом неопределенности."
        )
        return title, body
