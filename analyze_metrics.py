import os
import json
from datetime import datetime, timedelta
from collections import Counter
from openai import OpenAI

# Inicializa o cliente OpenAI com a API_KEY do ambiente
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("❌ ERRO: variável de ambiente OPENAI_API_KEY não encontrada. Configure-a no GitHub Actions Secrets.")

client = OpenAI(api_key=OPENAI_API_KEY)


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_best_times(videos_or_posts, views_key="views", likes_key="likes", comments_key="comments", time_key="publishedAt"):
    engagement_data = []
    for item in videos_or_posts:
        try:
            views = item.get(views_key, 0)
            likes = item.get(likes_key, 0)
            comments = item.get(comments_key, 0)
            total_engagement = views + likes + comments
            published_time = item.get(time_key) or item.get("timestamp")
            if published_time:
                dt = datetime.fromisoformat(published_time.replace("Z", "+00:00"))
                engagement_data.append((dt.hour, total_engagement))
        except Exception:
            pass

    hour_counter = Counter()
    for hour, engagement in engagement_data:
        hour_counter[hour] += engagement

    best_hours = [f"{h:02d}:00" for h, _ in hour_counter.most_common(2)]
    return best_hours


def summarize_performance(metadata, ganchos):
    youtube_videos = metadata["youtube"]["videos"]
    insta_posts = metadata["instagram"]["posts"]

    best_hours_youtube = extract_best_times(youtube_videos)
    best_hours_insta = extract_best_times(
        insta_posts,
        views_key="likes",
        likes_key="likes",
        comments_key="comments",
        time_key="timestamp"
    )

    summary = {
        "melhor_horario_youtube": best_hours_youtube,
        "melhor_horario_instagram": best_hours_insta,
        "top_titles_youtube": [
            v["title"] for v in sorted(youtube_videos, key=lambda x: x.get("views", 0), reverse=True)[:3]
        ],
        "top_captions_instagram": [
            p["caption"] for p in sorted(insta_posts, key=lambda x: x.get("likes", 0), reverse=True)[:3]
        ],
        "ganchos_existentes": list(ganchos.keys()),
    }
    return summary


def gerar_ganchos_com_ia(analise):
    prompt = f"""
    Gere um JSON criativo com base nas tendências e melhores horários detectados a seguir:
    {json.dumps(analise, indent=2, ensure_ascii=False)}

    O formato de saída DEVE ser exatamente assim:
    {{
      "gancho_youtube_1": {{
        "title": "😳 Eu não devia mostrar isso aqui...",
        "description": "Se ainda estiver disponível, tá no link da bio...",
        "tags": ["proibido", "descubra", "linknabio"]
      }},
      "gancho_youtube_2": {{
        "title": "🚨 Isso vai sair do ar em poucas horas!",
        "description": "Se você perdeu o último, nem adianta chorar depois...",
        "tags": ["urgente", "exclusivo", "linkfixado"]
      }},
      "gancho_instagram_1": {{
        "title": "👀 Você vai entender só depois que ver o link.",
        "description": "Não é o que parece... mas é exatamente o que você precisa ver hoje.",
        "tags": ["mistério", "curioso", "linknabio"]
      }},
      "gancho_instagram_2": {{
        "title": "🔥 Todo mundo tá comentando sobre isso!",
        "description": "Nem todo mundo vai gostar, mas você precisa ver.",
        "tags": ["viral", "descubra", "trending"]
      }},
      "melhor_horario_youtube": ["04:00", "18:00"],
      "melhor_horario_instagram": ["13:00", "21:00"],
      "data_geracao": "AAAA-MM-DD HH:MM:SS"
    }}

    Gere títulos e descrições autênticos, curtos e com apelo emocional.
    Use os melhores horários encontrados no JSON acima.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "Você é um criador especialista em virais de YouTube e Instagram."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )

        content = response.choices[0].message.content
        return json.loads(content)

    except Exception as e:
        print(f"⚠️ Erro ao gerar ganchos com IA: {e}")
        return {
            "erro": str(e),
            "fallback": {
                "melhor_horario_youtube": analise.get("melhor_horario_youtube", []),
                "melhor_horario_instagram": analise.get("melhor_horario_instagram", [])
            }
        }


def main():
    metadata = load_json("data/metrics.json")
    ganchos = load_json("gancho_data.json")

    analise = summarize_performance(metadata, ganchos)
    resultado = gerar_ganchos_com_ia(analise)

    resultado["data_geracao"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("ganchos_otimizados.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)

    print(json.dumps(resultado, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
