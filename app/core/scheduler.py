from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.db.session import SessionLocal
from app.services.integration_service import IntegrationService
from app.db.models import ERPConnection
from app.core.logging import log
import atexit

scheduler = BackgroundScheduler()

def poll_active_integrations():
    """Iterates through active ERP connections and triggers sync if interval reached."""
    db = SessionLocal()
    try:
        # For POC, we trigger all active ones. 
        # Production would track 'next_sync_at' in the DB.
        connections = db.query(ERPConnection).filter(ERPConnection.status == "active").all()
        
        for conn in connections:
            if conn.integration_mode == "sftp":
                # Use a specific service method for background runs
                log.info(f"Scheduled sync triggered for {conn.display_name}")
                IntegrationService.process_sftp_polling(conn.id, db)
            
            elif conn.integration_mode == "api_pull":
                # IntegrationService.process_api_pull(conn.id, db)
                pass
                
    except Exception as e:
        log.error(f"Scheduler Error: {str(e)}")
    finally:
        db.close()

def start_scheduler():
    """Initializes the integrated background worker engine."""
    if not scheduler.running:
        scheduler.add_job(
            func=poll_active_integrations,
            trigger=IntervalTrigger(minutes=5), # Default poll interval
            id='integration_poller',
            name='Poll ERP integrations',
            replace_existing=True
        )
        scheduler.start()
        log.info("Integrated Enterprise Scheduler started successfully (t2.micro optimized)")
        
        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown())
