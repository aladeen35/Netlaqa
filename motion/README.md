# Motion – معلومة على السريع | Quick Fact

فيديوهات موشن جرافيك (1080×1080) لـ LinkedIn. كل فيديو يحتوي معلومتين، ومدته 22 ثانية تقريباً. اللوقو ثابت أعلى اليسار طوال الفيديو.

- المحتوى الأصلي في `content/quick_facts.md`.
- `python3 build_tips.py` يحوّل المحتوى إلى `tips.json` (كل معلومتين في فيديو).
- `python3 render.py` يصدّر كل الفيديوهات إلى `output/`.
- `python3 render.py --id 01-02` يصدّر فيديو واحداً، و`--preview 01-02` يحفظ لقطات PNG فقط.

- `python3 add_music.py` يضيف الموسيقى الخلفية (`assets/audio/background.m4a`) ويحفظ النسخ النهائية في `final/`.

يحتاج Python و Pillow (مع raqm) و ffmpeg.
