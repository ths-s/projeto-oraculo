import os
import json
from datetime import datetime
from collections import Counter
from openai import OpenAI


# ===========================
# 🔹 DETECTA O PROVEDOR DE IA
# ===========================
AI_PROVIDER = os.getenv("GROQ_API_KEY", "groq").lower()

if AI_PROVIDER == "groq":
    base_url = "https://api.groq.com/openai/v1"
    api_key = os.getenv("GROQ_API_KEY")
    model_name = "openai/gpt-oss-20b"
elif AI_PROVIDER == "openai":
    base_url = "https://api.openai.com/v1"
    api_key = os.getenv("OPENAI_API_KEY")
    model_name = "gpt-5"
else:
    raise ValueError(f"❌ Provedor de IA desconhecido: {AI_PROVIDER}")

if not api_key:
    raise ValueError(f"❌ ERRO: chave da API para {AI_PROVIDER} não encontrada nos secrets do GitHub Actions.")

client = OpenAI(api_key=api_key, base_url=base_url)


# ===========================
# 🔹 FUNÇÕES AUXILIARES
# ===========================
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


# ===========================
# 🔹 GERA OS GANCHOS COM IA
# ===========================
import json

def gerar_ganchos_com_ia(analise):
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "Gere ganchos curtos de vídeos e horários otimizados em formato JSON."},
                {"role": "user", "content": f"Baseado na análise: {analise}"}
            ]
        )

        texto = response.choices[0].message.content.strip()

        if not texto:
            raise ValueError("Resposta da IA veio vazia.")

        # tenta validar o JSON
        try:
            return json.loads(texto)
        except json.JSONDecodeError:
            print("⚠️ IA retornou texto inválido, resposta bruta:")
            print(texto)
            raise ValueError("A resposta da IA não é um JSON válido.")

    except Exception as e:
        print(f"⚠️ Erro ao gerar ganchos com IA: {e}")
        return {
            "erro": str(e),
            "fallback": {
                "melhor_horario_youtube": ["20:00", "16:00"],
                "melhor_horario_instagram": []
            },
            "data_geracao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }



# ===========================
# 🔹 MAIN
# ===========================
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
