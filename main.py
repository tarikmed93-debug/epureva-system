import threading
import os
from database import init_db

def lancer_scheduler():
    import time
    import schedule
    from scheduler import job_quotidien
    print("⏰ Scheduler démarré — job tous les jours à 08:00")
    schedule.every().day.at("08:00").do(job_quotidien)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    init_db()
    print("🚀 Epureva System démarré")
    t = threading.Thread(target=lancer_scheduler, daemon=True)
    t.start()
    from dashboard import app
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
