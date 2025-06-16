import tkinter as tk
from tkinter import scrolledtext
from predictor import launch_browser_get_html, parse_racecard, score_horse


def run_prediction():
    url = url_entry.get().strip()
    if not url:
        output_text.insert(tk.END, "❌ Please enter a racecard URL.\n")
        return

    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, f"🔍 Fetching racecard from: {url}\n\n")

    try:
        html = launch_browser_get_html(url)
        horses = parse_racecard(html)

        if not horses:
            output_text.insert(tk.END, "❌ No horses found.\n")
            return

        for horse in horses:
            horse["score"] = score_horse(horse)

        ranked = sorted(horses, key=lambda x: x["score"], reverse=True)

        output_text.insert(tk.END, "🏇 Predicted Order:\n\n")
        for i, h in enumerate(ranked, 1):
            output_text.insert(
                tk.END,
                f"{i}. {h['name']} - Score: {h['score']:.1f} | "
                f"Form: {h['form']} | CD: {'Yes' if h['cd_win'] else 'No'} | "
                f"Rating: {h['rating']} | Jockey: {h['jockey']} ({h['jockey_win_pct']}%) | "
                f"Odds: {h['odds']}\n"
            )

        output_text.insert(tk.END, f"\n🥇 Most Likely Winner: {ranked[0]['name']}\n")

    except Exception as e:
        output_text.insert(tk.END, f"\n❌ Error: {e}\n")


# GUI layout
window = tk.Tk()
window.title("Horse Race Predictor")
window.geometry("900x600")

tk.Label(window, text="Enter IrishRacing Racecard URL:").pack(pady=5)

url_entry = tk.Entry(window, width=100)
url_entry.pack(pady=5)

tk.Button(window, text="Predict Winner", command=run_prediction).pack(pady=5)

output_text = scrolledtext.ScrolledText(window, width=110, height=30)
output_text.pack(padx=10, pady=10)

window.mainloop()

