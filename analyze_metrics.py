import json
from statistics import mean

# Caminhos
METRICS_PATH = "data/metrics.json"
METADATA_PATH = "metadata.json"
GANCHO_PATH = "gancho_data.json"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    print("📈 Analisando desempenho dos ganchos...")

    metrics = load_json(METRICS_PATH)
    metadata = load_json(METADATA_PATH)
    ganchos = load_json(GANCHO_PATH)

    # Dicionário para somar métricas por gancho
    analise = {}

    # 🔹 Analisar vídeos do YouTube
    for video in metrics["youtube"]["videos"]:
        for file_name, meta in metadata.items():
            if meta["youtube_id"] == video["video_id"]:
                gancho = meta["gancho"]
                analise.setdefault(gancho, {"views": [], "likes": [], "comments": []})
                analise[gancho]["views"].append(video["views"])
                analise[gancho]["likes"].append(video["likes"])
                analise[gancho]["comments"].append(video["comments"])

    # 🔹 Analisar posts do Instagram
    for post in metrics["instagram"]["posts"]:
        for file_name, meta in metadata.items():
            if meta["instagram_id"] == post["id"]:
                gancho = meta["gancho"]
                analise.setdefault(gancho, {"views": [], "likes": [], "comments": []})
                analise[gancho]["likes"].append(post["likes"])
                analise[gancho]["comments"].append(post["comments"])

    # 🔹 Calcular médias
    print("\n📊 Resultados por Gancho:")
    resumo = []
    for gancho, data in analise.items():
        avg_views = mean(data["views"]) if data["views"] else 0
        avg_likes = mean(data["likes"]) if data["likes"] else 0
        avg_comments = mean(data["comments"]) if data["comments"] else 0
        total_score = avg_views + (avg_likes * 5) + (avg_comments * 10)  # peso customizável

        resumo.append({
            "gancho": gancho,
            "titulo": ganchos[gancho]["title"],
            "views_medio": round(avg_views),
            "likes_medio": round(avg_likes),
            "comentarios_medio": round(avg_comments),
            "score": round(total_score)
        })

    # 🔹 Ordenar do melhor ao pior
    resumo.sort(key=lambda x: x["score"], reverse=True)

    # 🔹 Exibir top 3
    print("\n🏆 Top 3 Ganchos com Melhor Desempenho:")
    for r in resumo[:3]:
        print(f"\n{r['titulo']}")
        print(f"• Média de views: {r['views_medio']}")
        print(f"• Média de likes: {r['likes_medio']}")
        print(f"• Média de comentários: {r['comentarios_medio']}")
        print(f"• Score total: {r['score']}")

    # 🔹 Salvar relatório JSON
    with open("data/analise_ganchos.json", "w", encoding="utf-8") as f:
        json.dump(resumo, f, indent=2, ensure_ascii=False)

    print("\n✅ Análise concluída! Resultado salvo em data/analise_ganchos.json")

if __name__ == "__main__":
    main()
