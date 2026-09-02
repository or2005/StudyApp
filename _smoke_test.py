import time

from main import StudyApp

app = StudyApp()
app.update()

onboard = app.content.winfo_children()[0]
if hasattr(onboard, "name_var"):
    onboard.name_var.set("מיכל בדיקה")
    onboard.age_var.set("17")
    onboard.id_var.set("123456789")
    onboard._submit_details()
    app.update()

# wait until diagnostic screen is active
for _ in range(200):
    app.update()
    time.sleep(0.05)
    if hasattr(app.content.winfo_children()[0], "questions"):
        break

frame = app.content.winfo_children()[0]
for i in range(200):
    if not hasattr(frame, "questions") or frame.q_index >= len(frame.questions):
        break
    q = frame.questions[frame.q_index]
    frame.selected.set(q["answer"])
    frame._next_question()
    app.update()
    time.sleep(0.03)
    if app.content.winfo_children():
        frame = app.content.winfo_children()[0]

print("HAS_PROFILE", app.storage.has_profile())
if app.storage.get_diagnostic():
    d = app.storage.get_diagnostic()
    print("LEVEL", d.get("level"))
    print("WEAK_TOPICS", d.get("weak_topics"))
    print("ANSWERS", len(d.get("answers", [])))
else:
    print("DIAGNOSTIC_MISSING")

app.destroy()
