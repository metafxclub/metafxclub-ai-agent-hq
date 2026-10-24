"""HEAD baseline loop: regression fixture, never production-imported."""
def ai_trade_council_worker_loop(worker_id: str) -> None:
    """Run only Council votes; three instances form the bounded parallel round pool."""
    config = mission_worker_config()
    while not MISSION_WORKER_STOP.is_set():
        try:
            if load_operator_mode_record().get("mode") != "auto_guarded":
                MISSION_WORKER_WAKE.wait(config["idlePollSeconds"])
                MISSION_WORKER_WAKE.clear()
                continue
            mission = find_next_auto_mission(council_only=True)
            if mission:
                process_auto_mission(worker_id, mission)
                continue
            MISSION_WORKER_WAKE.wait(config["idlePollSeconds"])
            MISSION_WORKER_WAKE.clear()
        except DataIntegrityError:
            MISSION_WORKER_WAKE.wait(config["runnerUnavailableBackoffSeconds"])
            MISSION_WORKER_WAKE.clear()
        except Exception:
            append_audit({
                "type": "ai_trade_council.worker_error",
                "workerId": worker_id,
                "automaticRetry": False,
            })
            MISSION_WORKER_WAKE.wait(config["runnerUnavailableBackoffSeconds"])
            MISSION_WORKER_WAKE.clear()
