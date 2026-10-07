"""Tes tidak boleh memanggil LLM sungguhan, walaupun .env lokal berisi kunci Gemini."""
import os

# Diset sebelum app.config dibaca; load_dotenv tidak menimpa variabel yang sudah ada.
os.environ["LLM_PROVIDER"] = "none"
